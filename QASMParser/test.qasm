// quantum ripple-carry adder from Cuccaro et al, quant-ph/0410184
OPENQASM 2.0;
include "qelib1.inc";

gate majority a,b,c 
{ 
  cx c,b; 
  cx c,a; 
  ccx a,b,c; 
}

rgate unmaj a,b,c 
{ 
  ccx a,b,c; 
  cx c,a; 
  cx a,b;
  unmaj a,a,a
}

CBLOCK
{
  printf('%s', "Hello!");
  int A = 3;
  float C = 0.6;
  for (int i = 1; i < 3; i++) {
      printf("%s %d","hi",i)
  }
}

qreg cin[1];
qreg a[4];
qreg b[4];
qreg cout[1];
creg ans[5];

// set input states
// a = 0001
x a[0]; 
// b = 1111
x b;    
// add a to b, storing result in b

majority cin[0],b[0],a[0];
majority a[0],b[1],a[1];
majority a[1],b[2],a[2];
majority a[2],b[3],a[3];

cx a[3],cout[0];

unmaj a[2],b[3],a[3];
unmaj a[1],b[2],a[2];
unmaj a[0],b[1],a[1];
unmaj cin[0],b[0],a[0];

measure b[0] -> ans[0];
measure b[1] -> ans[1];
measure b[2] -> ans[2];
measure b[3] -> ans[3];

measure cout[0] -> ans[4];

creg loopVar[4];
measure b -> loopVar;

if (ans[0] == 1) { CBLOCK { printf("%i", 128); } };

U(0,0,lambda) a;

reset a;
reset b[2];