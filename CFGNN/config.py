import argparse


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vocab_size', type=int, default=100000,
                        help='Vocab size for training')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='Input batch size for training')
    parser.add_argument('--hidden_dim', type=int, default=128,
                        help='Dimension of hidden states')
    parser.add_argument('--max_node', type=int, default=150,
                        help='Maximum number of nodes')
    parser.add_argument('--max_token', type=int, default=20,
                        help='Maximum number of tokens')
    parser.add_argument('--learning_rate', type=float, default=0.001,
                        help='Learning rate')
    parser.add_argument('--epoch', type=int, default=10,
                        help='Epochs for training')
    parser.add_argument('--cpu', action='store_true', default=False,
                        help='Disables CUDA training')
    parser.add_argument('--gpu', type=int, default=0,
                        help='GPU ID for CUDA training')
    parser.add_argument('--save-model', action='store_true', default=False,
                        help='For Saving the current Model')
    args = parser.parse_args()
    return args
