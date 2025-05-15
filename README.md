# Ultimate Dice Roller

A modern, fantasy-themed, provably fair dice roller web app for tabletop RPGs, crypto games, and more.

## Features

- 🎲 **Provably Fair Dice Rolls** — Each roll generates a cryptographic proof that can be independently verified.
- ⚡ **Quick Roll Input** — Use simple expressions like `2d6+3`, `d20`, or `4d8-1` for instant results.
- 🧙 **Modern Fantasy UI** — Stylish interface using Bootstrap, custom CSS, Google Fonts (Cinzel, Fira Mono, Inter), and Bootstrap Icons.
- 📜 **Roll History** — View the last 10 rolls with timestamps, dice, results, modifiers, labels, and proof links.
- 🛡️ **Proof Verification** — Anyone can verify any roll using the proof and seeds, either in-app or externally.

## Tech Stack

- **Backend:** Python (Flask), MongoDB
- **Frontend:** Bootstrap 5, Bootstrap Icons, Google Fonts, Custom CSS

## Setup & Installation

1. **Clone the repo:**

   ```bash
   git clone https://github.com/TheCrazyGM/ultimate-dice.git
   cd ultimate-dice
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Start MongoDB:**
   Ensure you have a local MongoDB instance running (default: `mongodb://localhost:27017/`).
4. **Run the app:**

   ```bash
   source .venv/bin/activate
   python3 app.py
   # or
   flask run
   ```

5. **Visit:**
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

- **Quick Roll:** Enter dice expressions (e.g., `2d6+4`) and get results, totals, and proof links instantly.
- **Roll Dice Cards:** Use the preset dice cards for common dice types or custom dice.
- **Verify Proof:** Click any proof link or use the Verify Proof page to check the fairness of any roll.

## Credits

- UI/UX, concept, and code by [@TheCrazyGM](https://peakd.com/@thecrazygm)
- Inspired by fantasy RPGs and blockchain gaming communities.

---

<i>"With <span style='color:#e25555'>&#10084;&#65039;</span> by <a href="https://peakd.com/@thecrazygm">@TheCrazyGM</a>"</i>
