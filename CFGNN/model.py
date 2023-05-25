import torch
import torch.nn as nn
import torch.nn.functional as F
import pdb

class CFGNN(nn.Module):
    def __init__(self, opt):
        super(CFGNN, self).__init__()
        self.hidden_dim = opt.hidden_dim
        self.embedding = nn.Embedding(opt.vocab_size+2, opt.hidden_dim, padding_idx=1)
        self.node_lstm = nn.LSTM(self.hidden_dim, self.hidden_dim//2, bidirectional=True, batch_first=True)
        self.gate = Gate(self.hidden_dim, self.hidden_dim)
        self.back_gate = Gate(self.hidden_dim, self.hidden_dim)
        self.concat = nn.Linear(self.hidden_dim*2, self.hidden_dim)
        self.attention = GlobalAttention(self.hidden_dim*2, attn_type='mlp')
        # self.drop = nn.Dropout(0.3)
        self.fc_output = nn.Linear(self.hidden_dim*4, 1)

    def forward(self, x, edges, node_lens=None, token_lens=None, target=None):
        f_edges, b_edges = edges
        batch_size, num_node, num_token = x.size(0), x.size(1), x.size(2)
        x = self.embedding(x)  # [B, N, L, H]
        if token_lens is not None:
            x = x.view(batch_size*num_node, num_token, -1)
            # h_n = torch.zeros((1, batch_size*num_node, self.hidden_dim)).to(x.device)
            h_n = torch.zeros((2, batch_size*num_node, self.hidden_dim//2)).to(x.device)
            c_n = torch.zeros((2, batch_size*num_node, self.hidden_dim//2)).to(x.device)
            x, _ = self.node_lstm(x, (h_n, c_n))  # [B*N, L, H]
            x = x.view(batch_size, num_node, num_token, -1)

            x = self.average_pooling(x, token_lens)
        else:
            x = torch.mean(x, dim=2)  # [B, N, H]

        h = torch.zeros(x.size()).to(x.device)
        c = torch.zeros(x.size()).to(x.device)

        f_matrix = self.convert_to_matrix(batch_size, num_node, f_edges)

        for i in range(num_node):
            x_cur = x[:, i, :].squeeze()
            f_i = f_matrix[:, i, :].unsqueeze(1)
            h_last, c_last = f_i.bmm(h), f_i.bmm(c)
            h_i, c_i = self.gate(x_cur, h_last.squeeze(), c_last.squeeze())
            h[:, i, :], c[:, i, :] = h_i, c_i

        b_matrix = self.convert_to_matrix(batch_size, num_node, b_edges)
        for j in range(num_node):
            b_j = b_matrix[:, j, :].unsqueeze(1)
            h_temp = b_j.bmm(h)
            h[:, j, :] += h_temp.squeeze()

        h_b = torch.zeros(x.size()).to(x.device)
        c_b = torch.zeros(x.size()).to(x.device)

        b_matrix = self.convert_to_matrix(batch_size, num_node, f_edges)
        b_matrix = b_matrix.transpose(1, 2)
        for i in reversed(range(num_node)):
            x_cur = x[:, i, :].squeeze()
            b_i = b_matrix[:, i, :].unsqueeze(1)
            h_hat, c_hat = b_i.bmm(h_b), b_i.bmm(c_b)
            h_b[:, i, :], c_b[:, i, :] = self.back_gate(x_cur, h_hat.squeeze(), c_hat.squeeze())

        f_matrix = self.convert_to_matrix(batch_size, num_node, b_edges)
        f_matrix = f_matrix.transpose(1, 2)
        for j in range(num_node):
            f_j = f_matrix[:, j, :].unsqueeze(1)
            h_temp = f_j.bmm(h_b)
            h_b[:, j, :] += h_temp.squeeze()

        h = torch.cat([h, h_b], dim=2)
        if target is not None:
            # src = h[torch.arange(0,h.size(0)), target.reshape(-1), :]
            # h = self.drop(h)
            # h = nn.BatchNorm1d(h.size(1), affine=False).to(h.device)(h)
            output, weights = self.attention(h, node_lens, target)
            # output = self.drop(output)
            # print(node_lens)
            # print(target[:3])
            # print(weights[:3])
        else:
            output = torch.mean(h, dim=1)
        output = torch.sigmoid(self.fc_output(output))
        return output

    @staticmethod
    def average_pooling(data, input_lens):
        B, N, T, H = data.size()
        idx = torch.arange(T, device=data.device).unsqueeze(0).expand(B, N, -1)
        idx = idx < input_lens.unsqueeze(2)
        idx = idx.unsqueeze(3).expand(-1, -1, -1, H)
        ret = (data.float() * idx.float()).sum(2) / (input_lens.unsqueeze(2).float()+10**-32)
        return ret

    @staticmethod
    def convert_to_matrix(batch_size, max_num, m):
        matrix = torch.zeros((batch_size, max_num, max_num), dtype=torch.float, device=m.device)
        m -= 1
        b_select = torch.arange(batch_size).unsqueeze(1).expand(batch_size, m.size(1)).contiguous().view(-1)
        matrix[b_select, m[:, :, 1].contiguous().view(-1), m[:, :, 0].contiguous().view(-1)] = 1
        matrix[:, 0, 0] = 0
        return matrix


class Gate(nn.Module):
    def __init__(self, in_dim, mem_dim):
        super(Gate, self).__init__()
        self.in_dim = in_dim
        self.mem_dim = mem_dim
        self.ax = nn.Linear(self.in_dim, 3 * self.mem_dim)
        self.ah = nn.Linear(self.mem_dim, 3 * self.mem_dim)
        self.fx = nn.Linear(self.in_dim, self.mem_dim)
        self.fh = nn.Linear(self.mem_dim, self.mem_dim)

    def forward(self, inputs, last_h, pred_c):
        #pdb.set_trace()
        iou = self.ax(inputs) + self.ah(last_h)
        i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
        i, o, u = F.sigmoid(i), F.sigmoid(o), F.tanh(u)

        f = F.sigmoid(self.fh(last_h) + self.fx(inputs))
        fc = torch.mul(f, pred_c)

        c = torch.mul(i, u) + fc
        h = torch.mul(o, F.tanh(c))
        return h, c


class GlobalAttention(nn.Module):
    def __init__(self, dim, coverage=False, attn_type="mlp",
                 attn_func="softmax"):
        super(GlobalAttention, self).__init__()

        self.dim = dim
        assert attn_type in ["dot", "general", "mlp"], (
            "Please select a valid attention type (got {:s}).".format(
                attn_type))
        self.attn_type = attn_type
        assert attn_func in ["softmax", "sparsemax"], (
            "Please select a valid attention function.")
        self.attn_func = attn_func
        self.annotation = nn.Sequential(nn.Embedding(2, 1), nn.Linear(1, 1))
        if self.attn_type == "general":
            self.linear_in = nn.Linear(dim, dim, bias=False)
        elif self.attn_type == "mlp":
            self.linear_context = nn.Linear(dim, dim, bias=False)
            self.linear_query = nn.Linear(dim, dim, bias=True)
            self.v = nn.Linear(dim, 1, bias=False)
        # mlp wants it with bias
        out_bias = self.attn_type == "mlp"
        self.linear_out = nn.Linear(dim * 2, dim, bias=out_bias)

        if coverage:
            self.linear_cover = nn.Linear(1, dim, bias=False)

    def score(self, h_t, h_s):
        """
        Args:
          h_t (FloatTensor): sequence of queries ``(batch, tgt_len, dim)``
          h_s (FloatTensor): sequence of sources ``(batch, src_len, dim``
        Returns:
          FloatTensor: raw attention scores (unnormalized) for each src index
            ``(batch, tgt_len, src_len)``
        """

        # Check input sizes
        src_batch, src_len, src_dim = h_s.size()
        tgt_batch, tgt_len, tgt_dim = h_t.size()
        self.aeq(src_batch, tgt_batch)
        self.aeq(src_dim, tgt_dim)
        self.aeq(self.dim, src_dim)

        if self.attn_type in ["general", "dot"]:
            if self.attn_type == "general":
                h_t_ = h_t.view(tgt_batch * tgt_len, tgt_dim)
                h_t_ = self.linear_in(h_t_)
                h_t = h_t_.view(tgt_batch, tgt_len, tgt_dim)
            h_s_ = h_s.transpose(1, 2)
            # (batch, t_len, d) x (batch, d, s_len) --> (batch, t_len, s_len)
            return torch.bmm(h_t, h_s_)
        else:
            dim = self.dim
            wq = self.linear_query(h_t.view(-1, dim))
            wq = wq.view(tgt_batch, tgt_len, 1, dim)
            wq = wq.expand(tgt_batch, tgt_len, src_len, dim)

            uh = self.linear_context(h_s.contiguous().view(-1, dim))
            uh = uh.view(src_batch, 1, src_len, dim)
            uh = uh.expand(src_batch, tgt_len, src_len, dim)

            # (batch, t_len, s_len, d)
            wquh = torch.tanh(wq + uh)

            return self.v(wquh.view(-1, dim)).view(tgt_batch, tgt_len, src_len)

    def forward(self, memory_bank, memory_lengths=None, targets=None):

        # one step input
        source = torch.max(memory_bank, dim=1)[0]
        source = source.unsqueeze(1)

        batch, source_l, dim = memory_bank.size()
        batch_, target_l, dim_ = source.size()
        self.aeq(batch, batch_)
        self.aeq(dim, dim_)
        self.aeq(self.dim, dim)

        # compute attention scores, as in Luong et al.
        align = self.score(source, memory_bank)
        if targets is not None:
            # import pdb
            # pdb.set_trace()
            annotations = self.annotation(targets.unsqueeze(-1)).transpose(1, 2).squeeze(-1)
            align *= annotations

        if memory_lengths is not None:
            mask = self.sequence_mask(memory_lengths, max_len=align.size(-1))
            # mask[torch.arange(0, mask.size(0)), targets] = 0
            mask = mask.unsqueeze(1)  # Make it broadcastable.
            align.masked_fill_(~mask, -float('inf'))

        # Softmax or sparsemax to normalize attention weights
        if self.attn_func == "softmax":
            align_vectors = F.softmax(align.view(batch*target_l, source_l), -1)

        align_vectors = align_vectors.view(batch, target_l, source_l)

        # each context vector c_t is the weighted average
        # over all the source hidden states
        c = torch.bmm(align_vectors, memory_bank)
        concat_c = torch.cat([c, source], 2).view(batch*target_l, dim*2)
        attn_h = concat_c
        if self.attn_type in ["general", "dot"]:
            attn_h = torch.tanh(attn_h)

        attn_h = attn_h.squeeze(1)
        align_vectors = align_vectors.squeeze(1)

        return attn_h, align_vectors

    @staticmethod
    def aeq(*args):
        """
        Assert all arguments have the same value
        """
        arguments = (arg for arg in args)
        first = next(arguments)
        assert all(arg == first for arg in arguments), \
            "Not all arguments have the same value: " + str(args)

    @staticmethod
    def sequence_mask(lengths, max_len=None):
        """
        Creates a boolean mask from sequence lengths.
        """
        batch_size = lengths.numel()
        max_len = max_len or lengths.max()
        return (torch.arange(0, max_len, device=lengths.device)
                .type_as(lengths)
                .repeat(batch_size, 1)
                .lt(lengths.unsqueeze(1)))



