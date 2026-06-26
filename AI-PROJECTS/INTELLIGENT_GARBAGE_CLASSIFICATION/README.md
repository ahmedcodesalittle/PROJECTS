# Sortwise — Intelligent Garbage Classification

A full-stack waste classifier. A MobileNetV2 model (trained on Kaggle's
12-class Garbage Classification dataset) is served by a **Flask** API and
consumed by a **React** frontend. Upload a photo of an item → get its
material category, a confidence score, and which bin it belongs in.

```
garbage-classifier/
├── training/        # Kaggle notebook to train + export the model
├── backend/         # Flask API (loads the model, serves /api/predict)
│   └── models/      # <- put the trained model files here
└── frontend/        # React + Vite UI
```

## The 12 categories
paper · cardboard · biological · metal · plastic · green-glass ·
brown-glass · white-glass · clothes · shoes · batteries · trash

---

## Step 1 — Train the model (Kaggle GPU)

1. Make a new Kaggle Notebook.
2. **Add Input** → add *Garbage Classification (12 classes)* by Mostafa Abla.
3. **Settings → Accelerator → GPU** (T4 x2 or P100).
4. Paste the cells from `training/train_garbage_classifier.py` and Run All.
   (Each `===== CELL n =====` block is meant to be one notebook cell.)
5. Training takes roughly 30–60 min. When done, open the **Output** panel
   and download:
   - `garbage_model.keras`
   - `class_names.json`
6. Put both files into `backend/models/`.

Expect around **88–92%** validation accuracy with the two-phase
(transfer + fine-tune) setup. The most common confusion is between the three
glass colours — that's normal and visible in the confusion matrix it saves.

---

## Step 2 — Run the backend (Flask)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app.py
```

The API is now on `http://localhost:5000`.
Check `http://localhost:5000/api/health` — it should report
`"model_loaded": true`.

---

## Step 3 — Run the frontend (React)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` calls to
Flask automatically, so there's nothing else to configure.

---

## How it fits together

```
 Browser (React, :5173)
      │  POST /api/predict  (image file)
      ▼
 Flask API (:5000)
      │  resize → MobileNetV2 → softmax over 12 classes
      ▼
 { prediction, confidence, guidance, distribution }
```

The model's preprocessing (MobileNetV2 scaling) is baked into the saved graph,
so the backend only resizes to 224×224 — it never has to re-implement the
preprocessing, which is a common source of train/serve mismatch bugs.

## Tweaks you might want
- **Disposal guidance**: edit the `GUIDANCE` dict in `backend/app.py` to match
  your local council's bin names.
- **Different backbone**: swap `MobileNetV2` for `EfficientNetB0` in the
  training script for a small accuracy bump at the cost of speed.
- **Deploy**: build the frontend (`npm run build`) and serve the static files
  from Flask, or host the API on Render/Railway and the frontend on Vercel.
```
