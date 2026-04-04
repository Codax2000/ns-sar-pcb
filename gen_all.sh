
conda activate hardware_analysis

python ./scripts/registers.py
python ./scripts/diagrams.py

cd docs
mkdocs gh-deploy

cd ..