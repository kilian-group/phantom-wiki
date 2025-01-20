cmd_s="bash eval/rag_S.sh /home/jcl354/phantom-wiki/out/original_interactions"
echo $cmd_s
eval $cmd_s

cmd_m="bash eval/rag_M.sh /home/jcl354/phantom-wiki/out/original_interactions"
echo $cmd_m
eval $cmd_m

# cmd_l="bash eval/rag_L.sh /home/jcl354/phantom-wiki/out/large"
# echo $cmd_l
# eval $cmd_l