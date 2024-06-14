#include <algorithm>
#include <iostream>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <vector>

/*
This program opens a buffer and count occurrence of 5's.

*/

int main(int argc, char *argv[]) {
  int opt;
  std::string filename;
  int task_count = 0;
  int read_step = 0;

  while ((opt = getopt(argc, argv, "f:t:r:")) != -1) {
    switch (opt) {
    case 'f':
      filename = optarg;
      break;
    case 't':
      task_count = std::stoi(optarg);
      break;
    case 'r':
      read_step = std::stoi(optarg);
      break;
    default:
      std::cerr << "Usage: " << argv[0]
                << " -f filename -t task_count -r read_step\n";
      return EXIT_FAILURE;
    }
  }
  if (filename.empty() || task_count == 0 || read_step == 0) {
    std::cerr << "Usage: " << argv[0]
              << " -f filename -t task_count -r read_step\n";
    return EXIT_FAILURE;
  }

  FILE *file = fopen(filename.c_str(), "rb");
  if (!file) {
    perror("Failed to open file");
    return 1;
  }

  // Get file size
  fseek(file, 0, SEEK_END);
  long filesize = ftell(file);
  fseek(file, 0, SEEK_SET);
  printf("File size: %ld\n", filesize);
  fclose(file);

  const long chunk_size = filesize / task_count;

  printf("Chunk size: %ld\n", chunk_size);

  int total_count = 0;

#pragma omp parallel
  {
#pragma omp single
    {
      printf("Number of worker threads: %d\n",omp_get_thread_num());
      for (int i = 0; i < task_count; i++) {
#pragma omp task firstprivate(i) shared(total_count) shared(filename)
        {
          const long int offset = i * chunk_size;
          const long int end =
              (i == task_count - 1) ? filesize : offset + chunk_size;

          printf("Task %d reading chunk [%ld - %ld]\n", i, offset, end);

          FILE *_file = fopen(filename.c_str(), "rb");
          fseek(_file, offset, SEEK_SET);

          int _count = 0;

          std::vector<char> c(read_step);
          for (long int j = offset; j < end; j += read_step) {
            auto min = std::min(end - j, (long)read_step);
            fread(c.data(), 1, min, _file);
            for (int k = 0; k < min; k++) {
              if (c[k] == 5) {
                _count++;
              }
            }
          }

#pragma omp atomic
          total_count += _count;

          fclose(_file);

        } // end of task
      }   // end of for
    }     // end of single region
  }       // end of parallel region

  printf("Total occurrences of number 5: %d\n", total_count);

  return 0;
}
