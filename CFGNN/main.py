import data
import config
import os
import model
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
from sklearn.metrics import precision_recall_fscore_support
import warnings

warnings.simplefilter("ignore")

def train(opt, train_iter, valid_iter, device):
    net = model.CFGNN(opt).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(net.parameters(), lr=opt.learning_rate)
    # fw = open('res.txt', 'a')
    print('Start training...')
    for i in range(opt.epoch):
        total_loss = []
        total_accuracy = []
        net.train()
        for batch in tqdm(train_iter):
            x, m, t = batch.nodes, (batch.f_edges, batch.b_edges), batch.label.float()

            if isinstance(x, tuple):
                pred = net(x[0], m, x[1], x[2], batch.type)
            else:
                pred = net(x, m)
            pred = pred.squeeze()
            loss = criterion(pred, t)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss.append(loss.item())
            pred = (pred > 0.5).float()
            accuracy = (pred == t).float().mean()
            total_accuracy.append(accuracy.item())

        eval_loss = []
        eval_accuracy = []
        y_true, y_pred = [], []
        with torch.no_grad():
            net.eval()
            for step, batch in enumerate(valid_iter):
                x, m, t = batch.nodes, (batch.f_edges, batch.b_edges), batch.label.float()
                if isinstance(x, tuple):
                    pred = net(x[0], m, x[1], x[2], batch.type)
                else:
                    pred = net(x, m)
                pred = pred.squeeze()
                loss = criterion(pred, t)
                eval_loss.append(loss.item())
                pred = (pred > 0.5).float()
                accuracy = (pred == t).float().mean()
                eval_accuracy.append(accuracy.item())
                y_true.extend(t.tolist())
                y_pred.extend(pred.tolist())
        metrics = precision_recall_fscore_support(y_true, y_pred, average='binary')
        print(' Epoch: ' + str(i) + ' Train_Loss: {:.3f} '.format(sum(total_loss) / len(total_loss)) +
              ' Train_Accuracy: {:.3f} '.format(sum(total_accuracy) / len(total_accuracy)) +
              ' Val_Loss: {:.3f} '.format(sum(eval_loss) / len(eval_loss)) +
              ' Val_Accuracy: {:.3f} '.format(sum(eval_accuracy) / len(eval_accuracy)))
        print(" Precision: {:.3f} ".format(metrics[0]), " Recall: {:.3f} ".format(metrics[1]),
              " F_score: {:.3f} ".format(metrics[2]))

        os.makedirs('checkpoints/', exist_ok=True)
        torch.save(net, 'checkpoints/epoch-%d.pt' % i)

    # fw.close()
    return net


def main():
    opt = config.parse()
    device = torch.device("cuda:%d" % opt.gpu if torch.cuda.is_available() and not opt.cpu else "cpu")
    train_iter, test_iter = data.get_iterators(opt, device)
    train(opt, train_iter, test_iter, device)


if __name__ == '__main__':
    main()


