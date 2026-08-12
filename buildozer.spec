[app]
title = Top Sektirme Oyunu
package.name = topoyunu
package.domain = org.aile
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3==3.11.6,kivy==2.3.0
orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.permissions =
android.archs = arm64-v8a
