# Patent Oracle

Patent Oracle is an advanced AI-driven tool designed to generate novel, cross-disciplinary patent ideas. By leveraging local LLMs (via Ollama) and integrating with the European Patent Office (EPO) Open Patent Services, it helps inventors identify unprecedented opportunities at the intersection of diverse scientific fields.

---

## Description Multilingue

### English

Patent Oracle is a Python-based automation tool optimized for llama. It generates high-novelty patent concepts by combining three distinct scientific domains (e.g., Quantum Biology and Neuromorphic Materials). The system evaluates each idea for mechanism, novelty claims, and human impact, and can optionally perform a live prior-art search using the EPO API to check for existing patents.

### Arabic (العربية)

Patent Oracle هو اداة مبتكرة تعتمد على الذكاء الاصطناعي لتوليد افكار براءات اختراع غير مسبوقة. يقوم النظام بدمج ثلاثة مجالات علمية مختلفة (مثل البيولوجيا الكمومية والمواد العصبية) لابتكار مفاهيم تقنية جديدة. يوفر البرنامج تحليلا للالية العمل، وادعاءات الجدة، والاثر البشري، مع امكانية التحقق المباشر من وجود براءات اختراع مشابهة عبر قاعدة بيانات المكتب الاوروبي لبراءات الاختراع (EPO).

### French (Francais)

Patent Oracle est un outil d'automatisation base sur Python et optimise pour llama. Il genere des concepts de brevets hautement innovants en combinant trois domaines scientifiques distincts (par exemple, la biologie quantique et les materiaux neuromorphiques). Le systeme evalue chaque idee selon son mecanisme, ses revendications de nouveaute et son impact humain, et peut effectuer une recherche d'anteriorite en direct via l'API de l'OEB (Office Europeen des Brevets).

---

## Key Features

- **AI Idea Generation**: Uses Ollama (llama) to brainstorm unique patent ideas.
- **Cross-Domain Synthesis**: Merges disparate fields like "Fungal Network Computing" and "Cryogenic Robotics".
- **EPO Integration**: Real-time search for prior art to validate novelty.
- **Rich CLI Interface**: Beautifully formatted terminal output with progress bars and tables.
- **Auto-Export**: Saves results in both JSON and Markdown formats for further processing.

---

## Repository Structure

```
Patent_Oracle_Repository/
├── README.md
├── src/
│   └── patent_oracle_ollama54.py      # Main application source code
├── docs/
│   ├── Patent_Oracle.pdf              # Full documentation (PDF)
│   ├── Patent_Oracle_English_Presentation.pptx
│   ├── Patent_Oracle_Arabic_Presentation.pptx
│   └── Patent_Oracle_Presentation_FR.docx
└── legal/
    └── Demande_Officielle_de_Brevet_INAPI_Algerie.md
```

---

## Installation

```bash
pip install requests rich python-dotenv
```

## Usage

1. Ensure Ollama is running.
2. Run the script:

```bash
python src/patent_oracle_ollama54.py
```

---

## Author

**بلحلحالي محمد امين / BELHALHALI Med Amine**

- Address: 16, Cite Ibn Khamis, Tlemcen, Algeria
- Phone: +213 659 45 45 73
