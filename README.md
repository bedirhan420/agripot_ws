# AgriBot - Otonom Tarim ve Secici Hasat Robotu

ROS2 tabanli, Vizyon + Navigasyon + Manipulasyon disiplinlerini tek bir
mimaride birlestiren otonom hasat robotu projesi. Detaylar icin:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - katmanlar, veri akisi, tasarim gerekceleri
- [`docs/DESIGN_PATTERNS.md`](docs/DESIGN_PATTERNS.md) - SOLID + tasarim deseni katalogu
- [`docs/ROADMAP.md`](docs/ROADMAP.md) - fazli yol haritasi

## Onkosullar (Ubuntu VM uzerinde, VSCode Remote-SSH ile)

```bash
# ROS2 (Humble veya Jazzy) ve Gazebo (gz-sim / ros_gz) zaten kurulu varsayilir.
sudo apt install ros-$ROS_DISTRO-ros-gz ros-$ROS_DISTRO-robot-localization \
                  ros-$ROS_DISTRO-nav2-bringup ros-$ROS_DISTRO-moveit \
                  ros-$ROS_DISTRO-xacro ros-$ROS_DISTRO-cv-bridge \
                  ros-$ROS_DISTRO-message-filters

pip install ultralytics opencv-python numpy --break-system-packages
```

VSCode tarafinda onerilen eklentiler: **ROS** (ms-iot.vscode-ros),
**Python**, **CMake Tools**, **XML**. `.vscode/settings.json` bu proje
icin temel ayarlari zaten icerir.

## Derleme

```bash
cd agribot_ws
colcon build --symlink-install
source install/setup.bash
```

## Calistirma

```bash
# 1) Simulasyon (Gazebo dunyasi + robot + dinamik engeller + camur)
ros2 launch agribot_bringup agribot_simulation.launch.py

# 2) Algi (YOLOv8)
ros2 launch agribot_bringup agribot_perception.launch.py

# 3) Navigasyon (EKF + Nav2 + sira takibi State Machine)
ros2 launch agribot_bringup agribot_navigation.launch.py

# 4) Manipulasyon (MoveIt2 + hasat action sunucusu)
ros2 launch agribot_bringup agribot_manipulation.launch.py

# Hepsi birden:
ros2 launch agribot_bringup agribot_full_system.launch.py
```

## Paket Yapisi (ozet)

```
src/
├── agribot_core/            # framework-bagimsiz interface + ortak tipler (Strategy/Adapter/Observer/Command arayuzleri, ConfigManager)
├── agribot_msgs/            # ozel ROS2 mesaj/servis/action tanimlari
├── agribot_perception/      # YOLOv8 dedektor + olgunluk siniflandirma (Factory, Strategy)
├── agribot_navigation/      # sira takibi, EKF, State Machine + Strategy (row/waypoint/obstacle)
├── agribot_manipulation/    # MoveIt2 adapter, kuvvet kontrolu, Template Method + Command Pattern
├── agribot_description/     # URDF/Xacro robot modeli
├── agribot_simulation/      # Gazebo dunyasi, agac/meyve (kirilabilir eklem), dinamik engeller, MuJoCo alternatifi
└── agribot_bringup/         # launch dosyalari + config (is mantigi ICERMEZ)
```

Tam dizin agaci ve her dosyanin amaci icin `docs/ARCHITECTURE.md`'ye bakin.

## Onemli Tasarim Notlari

- **Sira takibi** 2D Lidar SLAM DEGIL, RGB-D point cloud tabanlidir (bkz.
  `agribot_navigation/row_following/row_detector.py`).
- **Kirilabilir eklem**, Gazebo'nun GERCEK `DetachableJoint` sistem
  eklentisiyle uygulanir (bkz. `agribot_simulation/models/apple_fruit/model.sdf`).
- **Nav2**, yalnizca donuslerde ve dinamik engel kacinmada kullanilir;
  sira-ici kontrol tamamen custom'dir (bkz. `docs/ARCHITECTURE.md` bolum 3).
- Kod tabaninin tamami **iskelet (skeleton)** seviyesindedir: mimari,
  arayuzler ve akis TAMDIR; `TODO` yorumlariyla isaretlenmis kisimlar
  (ornegin gercek MoveItPy cagrilari, egitilmis YOLO agirliklari) ROADMAP'e
  gore doldurulmalidir.
