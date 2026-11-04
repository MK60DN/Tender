from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "modeling"))
sys.path.insert(0, str(root / "experiments"))

import app.tender
import app.tender_models
import app.golden_bias
import app.world_tree
import app.mentalization
import app.preassessment
import app.knowledge_forest

print("modeling imports passed")
