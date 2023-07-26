"""Filtering."""

from multiprocessing import cpu_count

import argparse

from datasets import load_dataset,Dataset,load_dataset_builder

from filtering import DatasetFiltering

import json
import jsonlines

def check_num_proc(num_proc: int = -1) -> int:
    """
    Check the number of processors. Return a safe-checked value.

    Parameters
    ----------
    num_proc : int, optional
        Number of processors to use, by default -1

    Returns
    -------
    int
        Number of processors to use

    Raises
    ------
    ValueError
        If the input exceeds the number of processors available
    """
    maximum: int = cpu_count()
    if num_proc > maximum:
        raise ValueError(
            f"{num_proc} exceeds the maximum number ({maximum}) of processors"
        )

    if num_proc == -1:
        num_proc = maximum
    else:
        print(f"Using {num_proc} processors out of {maximum} can be slow")

    return num_proc


def parseArgs():
    parser = argparse.ArgumentParser(description="Filtering.")
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="oscar",
        help="Name of the dataset to load.",
    )
    parser.add_argument(
        "--config_name",
        type=str,
        default=None,
        help="Name of the dataset config to pass.",
    )
    parser.add_argument(
        "--data_files",
        type=str,
        default=None,
        help="'load_dataset' returns all files that match the Unix style pattern passed by 'data_files'",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Split of the dataset to consider.",
    )
    parser.add_argument(
        "--lang_dataset_id",
        type=str,
        default="zh",
        help="ID of the language in which the dataset is written.",
    )
    parser.add_argument(
        "--path_fasttext_model",
        type=str,
        default=None,
        help="Path to the Fasttext model used for language identification.",
    )
    parser.add_argument(
        "--path_sentencepiece_model",
        type=str,
        default="/mnt/vepfs/lingxin/pretrain/wulindong/code/dataprocessing-bigscience/zh.sp.model",
        help="Path to the Sentence Piece model used to tokenize text for perplexity scores.",
    )
    parser.add_argument(
        "--path_kenlm_model",
        type=str,
        default="/mnt/vepfs/lingxin/pretrain/wulindong/code/dataprocessing-bigscience/zh.arpa.bin",
        help="Path to the KenLM model used to compute perplexity scores.",
    )
    parser.add_argument(
        "--max_len_prefilter",
        type=int,
        default=None,
        help="Maximum length of documents to keep. Longer documents might crash the pipeline.",
    )
    parser.add_argument(
        "--remove_meta",
        action="store_true",
        help="Only keep text column in dataset.",
    )
    parser.add_argument(
        "--num_proc",
        type=int,
        default=10,
        help="Number of processes for multiprocessing. Default at the number of processors available.",
    )
    parser.add_argument(
        "--path_dir_save_dataset",
        type=str,
        default="/mnt/vepfs/lingxin/pretrain/wulindong/xiaohongshu_4/",
        help="Path to the directory where the filtered version of the dataset will be saved.",
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default="/mnt/vepfs/lingxin/pretrain/wulindong/xiaohongshu_3/note_20230309.json",
        help="Path to the directory where the dataset was be saved.",
    )
    args = parser.parse_args()
    return args

def ds_generator(input_path):
    with open(input_path,'r',encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                return 
            line = json.loads(line)
            yield line

def main():
    args = parseArgs()

    dataset = load_dataset('json', data_files=args.dataset_path,cache_dir='/mnt/vepfs/lingxin/pretrain/wulindong/cache_ppl3/')


    print("Filtering too-long documents")
    if args.max_len_prefilter is not None:
        dataset = dataset.filter(lambda x: len(x["text"]) < args.max_len_prefilter,
                                 num_proc=check_num_proc(args.num_proc))
    print("Too-long documents filtered")

    dataset_filtering = DatasetFiltering(
        dataset=dataset,
        lang_dataset_id=args.lang_dataset_id,
        path_fasttext_model=args.path_fasttext_model,
        path_sentencepiece_model=args.path_sentencepiece_model,
        path_kenlm_model=args.path_kenlm_model,
        num_proc=check_num_proc(args.num_proc),
        path_dir_save_dataset=args.path_dir_save_dataset,
    )

    print("Modifying documents")
    dataset_filtering.modifying_documents()
    print("Modifying step done")
    print("Filtering documents")
    dataset_filtering.filtering()
    print("Filtering step done")
    print("Saving dataset")
    dataset_filtering.save_dataset()
    print("Dataset saved")


if __name__ == "__main__":
    main()
