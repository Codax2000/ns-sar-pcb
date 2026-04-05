mkdir dumpfiles

find ./hdl_design/hdl_design.srcs -type f -name "*.sv" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  > dumpfiles/hdl.txt

find ./hdl_design/hdl_design.srcs -type f -name "*.svh" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> dumpfiles/hdl.txt

find ./hdl_design/hdl_design.srcs -type f -name "*.rdl" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> dumpfiles/hdl.txt

find ./scripts -type f -name "*.py" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> dumpfiles/scripts.txt

find . -maxdepth 4 -type f -name "*.md" \
  | xargs -I{} sh -c 'echo "===== Contents of {} =====" && cat "{}"' \
  >> dumpfiles/docs.txt

git log > dumpfiles/gitlog.txt