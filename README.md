# euroleague-fantasy-analyzer
A data-driven tool for EuroLeague Fantasy that analyzes player stats, values, and efficiency to help build optimal fantasy rosters. Includes metrics like pdk per credit, value rankings, and suggested lineups based on constraints (credits, positions, coach).


## 🚀 Features
- Parse and clean raw player data (CSV/JSON).
- Calculate value metrics:  
  - **pdk per credit** (fantasy points per cost unit).  
  - **efficiency per game**.  
  - **position-based rankings** (G, F, C).
- Identify **hidden gems** (cheap players with strong value).  
- Suggest **premium stars** and **balanced 12-player lineups**.  
- Include **coach selection** within credits cap.

---

## 📂 Structure
euroleague-fantasy-analyzer/
│── data/ # Raw player stats
│── notebooks/ # Jupyter/analysis notebooks
│── scripts/ # Python scripts (data cleaning, lineup builder)
│── results/ # Suggested lineups, reports
│── README.md



---

## ⚡ Usage
1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/euroleague-fantasy-analyzer.git
   cd euroleague-fantasy-analyzer
