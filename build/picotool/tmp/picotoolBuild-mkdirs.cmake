# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-src"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-build"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/tmp"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/src/picotoolBuild-stamp"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/src"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/src/picotoolBuild-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/src/picotoolBuild-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/picotool/src/picotoolBuild-stamp${cfgdir}") # cfgdir has leading slash
endif()
