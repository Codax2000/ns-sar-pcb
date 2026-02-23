find ./hdl_design/hdl_design.srcs -type f -name "*.sv" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  > hdl.txt

find ./hdl_design/hdl_design.srcs -type f -name "*.svh" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> hdl.txt

find ./scripts -type f -name "*.py" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> scripts.txt

find . -maxdepth 2 -type f -name "*.md" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> docs.txt

git log > gitlog.txt