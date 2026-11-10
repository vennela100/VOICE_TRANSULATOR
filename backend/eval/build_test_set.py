"""Create a 100-utterance text evaluation set; Telugu entries await review."""
import json
from pathlib import Path

OUT = Path(__file__).with_name("utterances.jsonl")
groups = {
    "hi": {
        "review": False,
        "phrases": [
            "सवा लाख रुपये कल दोपहर दो बजे भेजिए",
            "मुझे डेढ़ लाख रुपये चाहिए",
            "ढाई हजार रुपये अभी भेज दो",
            "पौने दो लाख रुपये का भुगतान है",
            "पांच हजार पचास रुपये खाते में डालें",
        ],
        "modifiers": ["कृपया ", "आज ", "कन्फर्म करें: ", "सुनिए, ", "एक बार फिर, "],
    },
    "te": {
        "review": True,
        "phrases": [
            "లక్ష రూపాయలు రేపు మధ్యాహ్నం రెండు గంటలకు పంపండి",
            "నాకు రెండు వేల రూపాయలు కావాలి",
            "ఐదు వేల రూపాయలు ఖాతాలో వేయండి",
            "రేపు ఉదయం పది గంటలకు కలుద్దాం",
            "ఈ నెల పదిహేనో తేదీన చెల్లించండి",
        ],
        "modifiers": ["దయచేసి ", "కన్ఫర్మ్ చేయండి: ", "వినండి, ", "మళ్లీ చెబుతున్నాను, ", "ఒకసారి "] ,
    },
    "hi-en": {
        "review": False,
        "phrases": [
            "कल meeting दो बजे है, please confirm",
            "सवा lakh rupees account में transfer करना",
            "payment पांच हजार रुपये से ज्यादा नहीं है",
            "deadline 15 June 2026 है, इसे change मत करना",
            "दो thousand रुपये advance भेजो, बाकी बाद में",
        ],
        "modifiers": ["कृपया ", "एक बात और, ", "मैं दोहरा रहा हूं: ", "ध्यान से सुनें, ", "फिर से: "],
    },
    "te-en": {
        "review": True,
        "phrases": [
            "రేపు meeting two PMకి ఉంది, please confirm",
            "ఐదు thousand rupees accountకి transfer చేయండి",
            "payment పదిహేను June 2026కి చేయండి",
            "మూడు thousand advance పంపండి, మిగతాది later",
            "deadline Friday, ten AM; change చేయకండి",
        ],
        "modifiers": ["దయచేసి ", "ఒక విషయం, ", "మళ్లీ చెబుతున్నాను: ", "జాగ్రత్తగా వినండి, ", "మరొకసారి: "],
    },
}
conditions = ["clean", "regional_pronunciation", "fast_speech", "background_noise", "phone_speaker_noise"]
with OUT.open("w", encoding="utf-8", newline="\n") as file:
    index = 0
    for language, group in groups.items():
        for phrase in group["phrases"]:
            for position, modifier in enumerate(group["modifiers"]):
                index += 1
                row = {
                    "case_id": f"BV-{index:03}", "language": language,
                    "source_text": modifier + phrase, "reference_transcript": "",
                    "expected_translation": "", "condition": conditions[position],
                    "native_review_required": group["review"],
                    "recording_path": "", "human_translation_rating": "",
                    "latency_ms": "", "completed": "", "critical_values_match": "",
                }
                file.write(json.dumps(row, ensure_ascii=False) + "\n")
print(f"Wrote 100 text cases to {OUT}")
