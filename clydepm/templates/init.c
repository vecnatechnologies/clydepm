/**
 * NOTICE: This software  source code and any of  its derivatives are the
 * confidential  and  proprietary   information  of  Vecna  Technologies,
 * Inc. (such source  and its derivatives are hereinafter  referred to as
 * "Confidential Information"). The  Confidential Information is intended
 * to be  used exclusively by  individuals or entities that  have entered
 * into either  a non-disclosure agreement or license  agreement (or both
 * of  these agreements,  if  applicable) with  Vecna Technologies,  Inc.
 * ("Vecna")   regarding  the  use   of  the   Confidential  Information.
 * Furthermore,  the  Confidential  Information  shall be  used  only  in
 * accordance  with   the  terms   of  such  license   or  non-disclosure
 * agreements.   All  parties using  the  Confidential Information  shall
 * verify that their  intended use of the Confidential  Information is in
 * compliance  with and  not in  violation of  any applicable  license or
 * non-disclosure  agreements.  Unless expressly  authorized by  Vecna in
 * writing, the Confidential Information  shall not be printed, retained,
 * copied, or  otherwise disseminated,  in part or  whole.  Additionally,
 * any party using the Confidential  Information shall be held liable for
 * any and  all damages incurred  by Vecna due  to any disclosure  of the
 * Confidential  Information (including  accidental disclosure).   In the
 * event that  the applicable  non-disclosure or license  agreements with
 * Vecna  have  expired, or  if  none  currently  exists, all  copies  of
 * Confidential Information in your  possession, whether in electronic or
 * printed  form, shall be  destroyed or  returned to  Vecna immediately.
 * Vecna  makes no  representations  or warranties  hereby regarding  the
 * suitability  of  the   Confidential  Information,  either  express  or
 * implied,  including  but not  limited  to  the  implied warranties  of
 * merchantability,    fitness    for    a   particular    purpose,    or
 * non-infringement. Vecna  shall not be liable for  any damages suffered
 * by  licensee as  a result  of  using, modifying  or distributing  this
 * Confidential Information.  Please email [info@vecnatech.com]  with any
 * questions regarding the use of the Confidential Information.
 */

#include <rtems.h>

//==================== POSIX_Init ====================================
void* POSIX_Init()
{
  // This function is necessary in able to call CONFIGURE_POSIX_INIT_THREAD_TABLE
  return NULL;
}

//==================== Init ====================================
rtems_task Init(
  rtems_task_argument argument
)
{
  while(true) {
    rtems_task_wake_after(1);

  }
}

/**************** START OF CONFIGURATION INFORMATION ****************/

#define CONFIGURE_APPLICATION_NEEDS_CONSOLE_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER

#define CONFIGURE_USE_IMFS_AS_BASE_FILESYSTEM
#define CONFIGURE_LIBIO_MAXIMUM_FILE_DESCRIPTORS   64
#define CONFIGURE_IMFS_MEMFILE_BYTES_PER_BLOCK    512
#define CONFIGURE_MAXIMUM_DRIVERS                  20

#define CONFIGURE_APPLICATION_NEEDS_LIBBLOCK
#define CONFIGURE_SWAPOUT_TASK_PRIORITY            2

#define CONFIGURE_INIT_TASK_STACK_SIZE           RTEMS_MINIMUM_STACK_SIZE
#define CONFIGURE_EXTRA_TASK_STACKS              RTEMS_MINIMUM_STACK_SIZE
#define CONFIGURE_RTEMS_INIT_TASKS_TABLE

#define CONFIGURE_MAXIMUM_TASKS                  rtems_resource_unlimited (20)
#define CONFIGURE_MAXIMUM_BARRIERS               rtems_resource_unlimited (10)
#define CONFIGURE_MAXIMUM_SEMAPHORES             rtems_resource_unlimited (20)
#define CONFIGURE_MAXIMUM_MESSAGE_QUEUES         rtems_resource_unlimited (4)
#define CONFIGURE_MAXIMUM_PARTITIONS             rtems_resource_unlimited (2)
#define CONFIGURE_MAXIMUM_USER_EXTENSIONS            8
#define CONFIGURE_MAXIMUM_TIMERS                     8
#define CONFIGURE_UNIFIED_WORK_AREAS

#if 1
#define CONFIGURE_MAXIMUM_POSIX_KEYS                 16
#define CONFIGURE_MAXIMUM_POSIX_KEY_VALUE_PAIRS      16
#define CONFIGURE_MAXIMUM_POSIX_THREADS              10
#define CONFIGURE_MAXIMUM_POSIX_CONDITION_VARIABLES  20
#define CONFIGURE_MAXIMUM_POSIX_MUTEXES              40
#endif

#define CONFIGURE_MICROSECONDS_PER_TICK              1000

#define CONFIGURE_SHELL_COMMANDS_INIT
#define CONFIGURE_SHELL_COMMANDS_ALL
#define CONFIGURE_POSIX_INIT_THREAD_TABLE

#define CONFIGURE_UNIFIED_WORK_AREAS
#define CONFIGURE_UNLIMITED_OBJECTS
#include <rtems/shellconfig.h>

#define CONFIGURE_INIT
#include <rtems/confdefs.h>

/****************  END OF CONFIGURATION INFORMATION  ****************/

