#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <signal.h>
int main(int argc,char **argv) {
  setbuf(stdout,NULL);
  if(argc!=2)return 2;
  printf("guard-fixture pid=%d mode=%s\n",getpid(),argv[1]);
  if(!strcmp(argv[1],"hold")) {
    pid_t child=fork(); if(child<0)return 3;
    printf("hold pid=%d child=%d\n",getpid(),child);
    sleep(30);return 0;
  }
  if(strcmp(argv[1],"aggregate"))return 2;
  pid_t children[2];
  for(int i=0;i<2;i++) {
    children[i]=fork();if(children[i]<0)return 3;
    if(!children[i]) {
      size_t size=40UL*1024*1024;
      volatile char *p=malloc(size);if(!p)return 4;
      for(size_t j=0;j<size;j+=4096)p[j]=1;
      printf("allocated child=%d bytes=%zu\n",getpid(),size);
      sleep(3);return 0;
    }
  }
  int failed=0;
  for(int i=0;i<2;i++){int status;if(waitpid(children[i],&status,0)<0)return 5;
    printf("child=%d status=%d\n",children[i],status);
    if(!WIFEXITED(status)||WEXITSTATUS(status))failed=1;}
  return failed?70:0;
}
