import csv
import json


def export_json(questions, filename="questions.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)


def export_csv(questions, filename="questions.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "question", "A", "B", "C", "D", "answer", "level", "topic"
        ])

        for q in questions:
            writer.writerow([
                q["question"],
                q["options"][0],
                q["options"][1],
                q["options"][2],
                q["options"][3],
                q["answer"],
                q["level"],
                q["topic"]
            ])