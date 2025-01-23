cmd_s="bash eval/zeroshot_rag_S.sh /home/jcl354/phantom-wiki/out/v0.3"
echo $cmd_s
eval $cmd_s
# cmd_s="bash eval/fewshot_rag_S.sh /home/jcl354/phantom-wiki/out/fewshotRag"

cmd_s="bash eval/cot_rag_S.sh /home/jcl354/phantom-wiki/out/v0.3"
echo $cmd_s
eval $cmd_s

cmd_m="bash eval/zeroshot_rag_M.sh /home/jcl354/phantom-wiki/v0.3"
echo $cmd_m
eval $cmd_m
# cmd_m="bash eval/fewshot_rag_M.sh /home/jcl354/phantom-wiki/out/fewshotRag"
cmd_m="bash eval/cot_rag_M.sh /home/jcl354/phantom-wiki/out/v0.3"
echo $cmd_m
eval $cmd_m

# cmd_l="bash eval/rag_L.sh /home/jcl354/phantom-wiki/out/large"
# echo $cmd_l
# eval $cmd_l