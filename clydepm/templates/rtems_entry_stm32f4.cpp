#include <stdio.h>
#include <rtems.h>

void clyde_entry(void) {
  printf("Hello from clyde\n");
  while (1) {
    rtems_task_wake_after(1000);
  }
}

extern "C"
rtems_task Init(rtems_task_argument argument) {
    clyde_entry();
}


/**************** START OF CONFIGURATION INFORMATION ****************/

#define CONFIGURE_APPLICATION_NEEDS_CONSOLE_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER

#define CONFIGURE_USE_IMFS_AS_BASE_FILESYSTEM
#define CONFIGURE_LIBIO_MAXIMUM_FILE_DESCRIPTORS   32
#define CONFIGURE_IMFS_MEMFILE_BYTES_PER_BLOCK    512
#define CONFIGURE_MAXIMUM_DRIVERS                  10

#define CONFIGURE_APPLICATION_NEEDS_LIBBLOCK
#define CONFIGURE_SWAPOUT_TASK_PRIORITY            2

#define CONFIGURE_INIT_TASK_STACK_SIZE           RTEMS_MINIMUM_STACK_SIZE
#define CONFIGURE_EXTRA_TASK_STACKS              RTEMS_MINIMUM_STACK_SIZE
#define CONFIGURE_RTEMS_INIT_TASKS_TABLE

#define CONFIGURE_MAXIMUM_TASKS                  rtems_resource_unlimited (4)
#define CONFIGURE_MAXIMUM_BARRIERS               rtems_resource_unlimited (4)
#define CONFIGURE_MAXIMUM_SEMAPHORES             rtems_resource_unlimited (10)
#define CONFIGURE_MAXIMUM_MESSAGE_QUEUES         rtems_resource_unlimited (4)
#define CONFIGURE_MAXIMUM_PARTITIONS             rtems_resource_unlimited (2)
#define CONFIGURE_MAXIMUM_USER_EXTENSIONS            8
#define CONFIGURE_MAXIMUM_TIMERS                     8
#define CONFIGURE_UNIFIED_WORK_AREAS

#if 1
#define CONFIGURE_MAXIMUM_POSIX_KEYS                 1
#define CONFIGURE_MAXIMUM_POSIX_KEY_VALUE_PAIRS      1
#define CONFIGURE_MAXIMUM_POSIX_THREADS              1
#define CONFIGURE_MAXIMUM_POSIX_CONDITION_VARIABLES  2
#define CONFIGURE_MAXIMUM_POSIX_MUTEXES              4
#endif

#define CONFIGURE_MICROSECONDS_PER_TICK              1000

#define CONFIGURE_SHELL_COMMANDS_INIT
#define CONFIGURE_SHELL_COMMANDS_ALL

#define CONFIGURE_UNIFIED_WORK_AREAS
#define CONFIGURE_UNLIMITED_OBJECTS
#include <rtems/shellconfig.h>

#define CONFIGURE_INIT
#include <rtems/confdefs.h>

/****************  END OF CONFIGURATION INFORMATION  ****************/
