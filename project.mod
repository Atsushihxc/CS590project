set SCHOOL;
set RACES;
set BLOCK;

var A{i in BLOCK, j in SCHOOL, k in RACES}, >=0, integer;
var P{k in RACE, j in SCHOOL}, >=0;

## race[k,j] # race k in school j
## sum{k in RACES} races[k,j]<=L[j]

param s{i in BLOCK, k in RACES};
param d{i in BLOCK, j in SCHOOL};
param Dm{i in BLOCK};
param L{j in SCHOOL};
param B{k in RACES};


minimize difference: sum{k in RACE, j in SCHOOL} (abs(P[j,k]-B[k]));

s.t. allocation{i in BLOCK, k in RACES}: sum{j in SCHOOL} A[i,j,k]=1;

s.t. distance{i in BLOCK, k in RACES}: sum{j in SCHOOL} A[i,j,k]*d[i,j] <= Dm[i];

s.t. total_students{j in SCHOOL}: sum{i in STUDENT, k in RACES} A[i,j,k] * s[i,k]<=L[j];

s.t. composition{j in SCHOOL, k in RACES}: P[j,k] =


