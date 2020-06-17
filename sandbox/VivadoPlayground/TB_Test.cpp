#include "HLS_Test.h"
#include <iostream>

int main(int argc, char const *argv[])
{
  if (hls_main(1, 2, 3) == 1 + 2 * 3) {
    std::cout << "----- Test is successful -----" << std::endl;
    return 0;
  } else {
    std::cout << "----- Test has failed -----" << std::endl;
    return -1;
  }
  
}