# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-src"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-build"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/tmp"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/src/picotool-populate-stamp"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/src"
  "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/src/picotool-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/src/picotool-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/ricardo/Documents/Personal/T_H_LCD_rp2040/build/_deps/picotool-subbuild/picotool-populate-prefix/src/picotool-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
