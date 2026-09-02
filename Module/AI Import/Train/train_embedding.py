from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from sentence_transformers import InputExample, SentenceTransformer, losses
from torch.utils.data import DataLoader

from common import read_jsonl, set_seed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/training.yaml")
    parser.add_argument("--train", default="../Data/processed/train.jsonl")
    parser.add_argument("--validation", default="../Data/processed/validation.jsonl")
    parser.add_argument("--output")
    args = parser.parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    set_seed(int(config["seed"]))
    records = read_jsonl([Path(args.train).resolve()])
    if len(records) < 20:
        raise ValueError("Dữ liệu quá ít để fine-tune an toàn. Cần tối thiểu 20 mẫu; nên có >=500 feedback đã xác nhận.")
    model = SentenceTransformer(config["base_model"])
    model.max_seq_length = int(config["max_seq_length"])
    examples = [InputExample(texts=[f"query: {item['source']}", f"passage: {item['target_text']}"])
                for item in records]
    loader = DataLoader(examples, shuffle=True, batch_size=int(config["batch_size"]))
    objective = losses.MultipleNegativesRankingLoss(model)
    output = Path(args.output or config["output_dir"]).resolve()
    warmup = max(1, int(len(loader) * int(config["epochs"]) * float(config["warmup_ratio"])))
    model.fit(train_objectives=[(loader, objective)], epochs=int(config["epochs"]), warmup_steps=warmup,
              optimizer_params={"lr": float(config["learning_rate"])}, output_path=str(output),
              checkpoint_path=str(output.parent / (output.name + "-checkpoints")), checkpoint_save_steps=100,
              show_progress_bar=True)
    metadata = {"base_model": config["base_model"], "seed": config["seed"], "epochs": config["epochs"],
                "training_examples": len(records), "prefix_contract": "query:/passage:"}
    (output / "training-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Model saved: {output}")


if __name__ == "__main__":
    main()

