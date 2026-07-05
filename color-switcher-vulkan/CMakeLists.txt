cmake_minimum_required(VERSION 3.10)
project(ColorSwitcherVulkan)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimize for maximum performance
set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")

# Find Vulkan
find_package(Vulkan REQUIRED)

# Find GLFW
find_package(glfw3 REQUIRED)

# Add executable
add_executable(color-switcher color-switcher.cpp)

# Link libraries
target_link_libraries(color-switcher
    Vulkan::Vulkan
    glfw
)

# Set output directory
set_target_properties(color-switcher PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Platform-specific settings
if(APPLE)
    target_compile_definitions(color-switcher PRIVATE
        VK_USE_PLATFORM_MACOS_MVK
        VK_ENABLE_BETA_EXTENSIONS
    )
    # Link against Metal framework on macOS
    target_link_libraries(color-switcher "-framework Metal" "-framework Cocoa" "-framework QuartzCore")
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(color-switcher PRIVATE /W4)
else()
    target_compile_options(color-switcher PRIVATE -Wall -Wextra -Wpedantic)
endif()
