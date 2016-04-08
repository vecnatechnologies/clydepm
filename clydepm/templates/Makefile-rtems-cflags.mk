#
#  RTEMS_MAKEFILE_PATH is typically set in an environment variable
#

PGM=${ARCH}/nextgen.exe

# C source names
CSRCS = init.c          

COBJS = $(CSRCS:%.c=${ARCH}/%.o)

PROJECT_ROOT=$(RTEMS_MAKEFILE_PATH)


include $(RTEMS_MAKEFILE_PATH)/Makefile.inc
include $(RTEMS_CUSTOM)
include $(PROJECT_ROOT)/make/leaf.cfg

INC_PATH=$(RTEMS_MAKEFILE_PATH)/lib/include
BSP_PATH=$(INC_PATH)/bsp


OBJS= $(COBJS) $(CXXOBJS) $(ASOBJS) 

all:    ${ARCH} $(PGM)

$(PGM): $(OBJS)
	$(make-cxx-exe)
	
build-clyde-rtems-demo: 
	CFLAGS="${CFLAGS}" clyde build --platform rtems 

CFLAGS+= -I. -I$(BSP_PATH) -I$(INC_PATH)

print-cflags:
	@echo ${CFLAGS}

print-compiler:
	@echo ${CC}

print-link:
	@echo ${LINK.cc} 

print-link-libs:
	@echo $(LINK_LIBS)
	
print-cpu-cflags:
	@echo $(CPU_CFLAGS)
