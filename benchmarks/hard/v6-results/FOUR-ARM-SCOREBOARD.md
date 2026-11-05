COMMON SET (single-shot): 71 tasks
arm        strict  content
contour     43/71     48/71 
basalt      49/71     49/71 
codex       49/71     49/71 
grok        59/71     59/71 

CONTOUR-ONLY loop tasks (6): strict 1/6 mean 0.625

McNemar exact (strict, paired on common set):
  contour  vs basalt  : +6/-12  p=0.2379  (n=71)
  grok     vs codex   : +11/-1  p=0.0063  (n=71)
  grok     vs contour : +17/-1  p=0.0001  (n=71)
  codex    vs basalt  : +2/-2  p=1.0000  (n=71)
  grok     vs basalt  : +11/-1  p=0.0063  (n=71)
  contour  vs codex   : +5/-11  p=0.2101  (n=71)

Per-category strict on common set:
cat   contour   basalt    codex     grok
A        5/9       7/9       7/9       6/9  
B        2/7       7/7       6/7       7/7  
C        6/8       5/8       5/8       6/8  
D        3/3       3/3       3/3       3/3  
E       10/10      9/10     10/10     10/10 
F        2/6       1/6       0/6       5/6  
G        5/6       5/6       5/6       5/6  
H        3/5       0/5       1/5       3/5  
I        5/6       6/6       6/6       6/6  
J        1/7       5/7       5/7       6/7  
K        1/4       1/4       1/4       2/4  
