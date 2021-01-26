#include "HLS_Test.h"

char hls_main(char v1, char v2, char v3) {
#ifndef __SYNTHESIS__
  return v1 + v2 * v3;
#endif
#ifdef __SYNTHESIS__
  return v1 + v2 * v3 + 1;
#endif 
}