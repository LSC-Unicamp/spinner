#include <iostream>
#include <mpi.h>
#include <vector>

// Function to count occurrences of '5' in a vector of characters
int count_occurrences(const std::vector<char> &buffer) {
  int count = 0;
  for (char c : buffer) {
    if (c == 5) {
      count++;
    }
  }
  return count;
}

int main(int argc, char *argv[]) {
  MPI_Init(&argc, &argv);

  int rank, size;
  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  if (argc != 3) {
    if (rank == 0) {
      std::cerr << "Usage: " << argv[0] << " <filename> <read_step>\n";
    }
    MPI_Finalize();
    return EXIT_FAILURE;
  }

  std::string filename = argv[1];
  int read_step = std::stoi(argv[2]);
  int task_count = size;

  MPI_File file;
  MPI_File_open(MPI_COMM_WORLD, filename.c_str(), MPI_MODE_RDONLY,
                MPI_INFO_NULL, &file);

  MPI_Offset filesize;
  MPI_File_get_size(file, &filesize);
  if (rank == 0) {
    std::cout << "File size: " << filesize << "\n";
  }

  const MPI_Offset chunk_size = filesize / task_count;
  if (rank == 0) {
    std::cout << "Chunk size: " << chunk_size << "\n";
  }

  MPI_Offset offset = rank * chunk_size;
  MPI_Offset end = (rank == task_count - 1) ? filesize : offset + chunk_size;

  std::vector<char> buffer(read_step);
  int local_count = 0;

  for (MPI_Offset i = offset; i < end; i += read_step) {
    MPI_Offset current_read_size = std::min(end - i, (MPI_Offset)read_step);
    MPI_File_read_at(file, i, buffer.data(), current_read_size, MPI_BYTE,
                     MPI_STATUS_IGNORE);

    for (MPI_Offset j = 0; j < current_read_size; ++j) {
      if (buffer[j] == 5) {
        local_count++;
      }
    }
  }

  int total_count = 0;
  MPI_Reduce(&local_count, &total_count, 1, MPI_INT, MPI_SUM, 0,
             MPI_COMM_WORLD);

  if (rank == 0) {
    std::cout << "Total occurrences of number 5: " << total_count << "\n";
  }

  MPI_File_close(&file);
  MPI_Finalize();

  return 0;
}
