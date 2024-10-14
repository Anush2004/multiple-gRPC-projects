import sys, os
import torch
from torch import nn
import argparse


DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)
torch.set_default_device(DEVICE)


from dataset import sample_split_sentences
from lm import LanguageModel

def get_args():
    parser = argparse.ArgumentParser(description="Choose a model to instantiate")
    parser.add_argument(
        "model_choice",
        type=int,
        choices=[0, 1, 2, 3],
        help="0: NNLM, 1: RNN, 2: Transformer",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()

    SENTENCEFILE = "../dataset/sentences.txt"
    NNLMFILE = "../models/nnlm.pth"
    RNNFILE = "../models/rnn.pth"
    TRANSFILE = "../models/trans.pth"
    PERPLEXITY_TRAIN_1 = "../perplexities/2022101121-LM1-train-perplexity.txt"
    PERPLEXITY_VAL_1 = "../perplexities/2022101121-LM1-val-perplexity.txt"
    PERPLEXITY_TEST_1 = "../perplexities/2022101121-LM1-test-perplexity.txt"
    PERPLEXITY_TRAIN_2 = "../perplexities/2022101121-LM2-train-perplexity.txt"
    PERPLEXITY_VAL_2 = "../perplexities/2022101121-LM2-val-perplexity.txt"
    PERPLEXITY_TEST_2 = "../perplexities/2022101121-LM2-test-perplexity.txt"
    PERPLEXITY_TRAIN_3 = "../perplexities/2022101121-LM3-train-perplexity.txt"
    PERPLEXITY_VAL_3 = "../perplexities/2022101121-LM3-val-perplexity.txt"
    PERPLEXITY_TEST_3 = "../perplexities/2022101121-LM3-test-perplexity.txt"

    DIRNAME = os.path.dirname(__file__)
    ABS_INPATH = os.path.join(DIRNAME, SENTENCEFILE)
    ABS_NNLM_PATH = os.path.join(DIRNAME, NNLMFILE)
    ABS_RNN_PATH = os.path.join(DIRNAME, RNNFILE)
    ABS_TRANS_PATH = os.path.join(DIRNAME, TRANSFILE)
    ABS_PERPLEXITY_PATH_TRAIN_1 = os.path.join(DIRNAME, PERPLEXITY_TRAIN_1)
    ABS_PERPLEXITY_PATH_VAL_1 = os.path.join(DIRNAME, PERPLEXITY_VAL_1)
    ABS_PERPLEXITY_PATH_TEST_1 = os.path.join(DIRNAME, PERPLEXITY_TEST_1)
    ABS_PERPLEXITY_PATH_TRAIN_2 = os.path.join(DIRNAME, PERPLEXITY_TRAIN_2)
    ABS_PERPLEXITY_PATH_VAL_2 = os.path.join(DIRNAME, PERPLEXITY_VAL_2)
    ABS_PERPLEXITY_PATH_TEST_2 = os.path.join(DIRNAME, PERPLEXITY_TEST_2)
    ABS_PERPLEXITY_PATH_TRAIN_3 = os.path.join(DIRNAME, PERPLEXITY_TRAIN_3)
    ABS_PERPLEXITY_PATH_VAL_3 = os.path.join(DIRNAME, PERPLEXITY_VAL_3)
    ABS_PERPLEXITY_PATH_TEST_3 = os.path.join(DIRNAME, PERPLEXITY_TEST_3)

    sys.path.append(ABS_INPATH)
    sys.path.append(ABS_NNLM_PATH)
    sys.path.append(ABS_RNN_PATH)
    sys.path.append(ABS_TRANS_PATH)
    sys.path.append(ABS_PERPLEXITY_PATH_TRAIN_1)
    sys.path.append(ABS_PERPLEXITY_PATH_VAL_1)
    sys.path.append(ABS_PERPLEXITY_PATH_TEST_1)
    sys.path.append(ABS_PERPLEXITY_PATH_TRAIN_2)
    sys.path.append(ABS_PERPLEXITY_PATH_VAL_2)
    sys.path.append(ABS_PERPLEXITY_PATH_TEST_2)
    sys.path.append(ABS_PERPLEXITY_PATH_TRAIN_3)
    sys.path.append(ABS_PERPLEXITY_PATH_VAL_3)
    sys.path.append(ABS_PERPLEXITY_PATH_TEST_3)


    NUM_SENTENCES = 1000
    print(f"Using device: {DEVICE}")

    train_dl, val_dl, test_dl, vocab = sample_split_sentences(ABS_INPATH, (0.7, 0.2, 0.1), NUM_SENTENCES, 5, 64, True)
    print(f"VOCAB SIZE: {vocab.VOCAB_SIZE}")
    print(f"EMBEDDING SIZE: {vocab.EMBEDDING_SIZE}")
    loss_fn = nn.NLLLoss(reduction='sum')

    optim = torch.optim.Adam

    if args.model_choice == 0:
        print("Instantiating NNLM model...")
        lm = LanguageModel("NNLM", ABS_NNLM_PATH, loss_fn, optim, vocab, 300, 0.2, 5)
        lm.train_and_test(train_dl, val_dl, test_dl)
        lm.calculate_perplexities(train_dl, ABS_PERPLEXITY_PATH_TRAIN_1)
        lm.calculate_perplexities(val_dl, ABS_PERPLEXITY_PATH_VAL_1)
        lm.calculate_perplexities(test_dl, ABS_PERPLEXITY_PATH_TEST_1)

    else:
        train_dl, val_dl, test_dl, vocab = sample_split_sentences(ABS_INPATH, (0.7, 0.2, 0.1), NUM_SENTENCES, -1, 64, False)

        if args.model_choice == 1:
            print("Instantiating RNN model...")
            lm = LanguageModel("RNN", ABS_RNN_PATH, loss_fn, optim, vocab, 300, 0.2)
            lm.train_and_test(train_dl, val_dl, test_dl)
            lm.calculate_perplexities(train_dl, ABS_PERPLEXITY_PATH_TRAIN_2)
            lm.calculate_perplexities(val_dl, ABS_PERPLEXITY_PATH_VAL_2)
            lm.calculate_perplexities(test_dl, ABS_PERPLEXITY_PATH_TEST_2)

        elif args.model_choice == 2:
            print("Instantiating Transformer Decoder model...")
            lm = LanguageModel("TRANS", ABS_TRANS_PATH, loss_fn, optim, vocab, 300, 0.2)
            lm.train_and_test(train_dl, val_dl, test_dl)
            lm.calculate_perplexities(train_dl, ABS_PERPLEXITY_PATH_TRAIN_3)
            lm.calculate_perplexities(val_dl, ABS_PERPLEXITY_PATH_VAL_3)
            lm.calculate_perplexities(test_dl, ABS_PERPLEXITY_PATH_TEST_3)

