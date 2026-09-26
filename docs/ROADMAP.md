# AgriBot - Yol Haritasi

Her faz bir onceki fazin CALISIR bir ciktisi uzerine insa edilir; boylece
her asamada demo edilebilir bir sonuc elde edilir ("sürekli entegrasyon"
zihniyeti).

## Faz 0 - Ortam Kurulumu ve Workspace Iskeleti
- VSCode Remote-SSH + ROS extension'in Ubuntu VM'e baglanmasi.
- `colcon build --symlink-install` ile workspace'in derlenmesi.
- `ament_flake8` / `ament_pep257` / `black` ile lint/format standardinin
  CI'a (veya en azindan pre-commit'e) baglanmasi.
- **Definition of Done**: `colcon build` hatasiz tamamlanir, tum
  paketler `ros2 pkg list` ciktisinda gorunur.

## Faz 1 - Robot Modeli ve Temel Simulasyon Ortami
- `agribot_description` URDF/Xacro'sunun Gazebo'ya spawn edilmesi.
- Klavye teleop (`ros2 run teleop_twist_keyboard`) ile temel hareket testi.
- **DoD**: Robot bos bir dunyada teleop ile surulebiliyor, `/wheel/odometry`
  yayinlaniyor.

## Faz 2 - Zemin Fiziği ve Dinamik Engel Simülasyonu
- `mud_ground_plane` modelinin dunyaya eklenmesi, farkli mu1/mu2 ile test.
- `dynamic_obstacle_spawner.py` ile actor + random-walk box senaryolarinin
  calistirilmasi.
- **DoD**: Robot camurlu bolgede gozle gorulur tekerlek kaymasi yasiyor;
  en az bir dinamik engel sahnede hareket ediyor.

## Faz 3 - Sıra Takibi ve Sensor Fuzyonu (Navigasyon)
- `RowDetector` algoritmasinin gercek/simule point cloud ile ayarlanmasi.
- `robot_localization` EKF'nin devreye alinmasi (ya da `LightweightEKF`
  ile prototipleme).
- Nav2'nin YALNIZCA donus/engel-kacinma icin entegrasyonu.
- **DoD**: Robot iki agac sirasi arasinda MUDAHALESIZ ilerleyebiliyor.

## Faz 4 - Bilgisayarli Goru Boru Hatti (YOLOv8)
- Elma veri setinin toplanmasi/etiketlenmesi (ya da acik bir veri setinin
  transfer-learning ile uyarlanmasi).
- `YOLOv8Detector` + `PerceptionNode`'un devreye alinmasi.
- `HsvThresholdMaturityClassifier`'in gercek meyvelerle kalibrasyonu.
- **DoD**: `/agribot/perception/detections` dogru bounding-box ve 3D
  konumla yayinlaniyor.

## Faz 5 - Agac/Meyve Modelleri ve Kirilabilir Eklemler
- Blender'da detayli agac/elma mesh'lerinin olusturulmasi.
- `DetachableJoint` eklentisinin gercek sahnede test edilmesi.
- **DoD**: Manuel bir ROS2 servis cagrisiyla elma agactan fiziksel
  olarak ayrilip yere dusuyor.

## Faz 6 - Manipulasyon ve Hassas Hasat (MoveIt2)
- `agribot_moveit_config` paketinin MoveIt Setup Assistant ile uretilmesi.
- `MoveIt2Adapter` icindeki `TODO`'larin gercek `MoveItPy` cagrilariyla
  doldurulmasi.
- `ForceController`'in gercek/simule F/T sensoruyle kalibrasyonu.
- (Opsiyonel, MuJoCo secildiyse) mujoco_ros'a `/mujoco/set_equality_active`
  ozel servisinin eklenmesi.
- **DoD**: Kol, sabit duran bir elmaya ulasip simule kuvvet uygulayarak
  onu koparabiliyor.

## Faz 7 - Sistem Entegrasyonu, Test ve Optimizasyon
- Tum `state_machine` gecislerinin uctan uca senaryoda dogrulanmasi
  (sira takibi -> tespit -> yaklasma -> hasat -> devam -> donus -> home).
- `pytest` + `launch_testing` ile birim/entegrasyon testleri
  (ozellikle `MissionContext`, `HarvestPlanner`, `RowDetector` saf-Python
  oldugu icin rclpy olmadan test edilebilir).
- Performans profiling (algi dongusu gecikmesi, kontrol dongusu jitter'i).
- Kod optimizasyonu: gereksiz kopyalamalarin (numpy array) azaltilmasi,
  YOLOv8 icin TensorRT/ONNX export degerlendirmesi.
- Saha/donanim geçişi icin sensor kalibrasyon ve checklist hazirligi.
- **DoD**: Simulasyonda, farkli camur seviyeleri ve dinamik engel
  yogunluklariyla en az 10 ardisik uctan-uca hasat dongusu basariyla
  tamamlaniyor.

---

### Onerilen Sprint Uzunlugu
Her faz, tek gelistiricili bir projede yaklasik **1-2 hafta**lik bir
sprint'e karsilik gelecek sekilde tasarlanmistir; ekip buyudukce fazlar
paralellestirilebilir (ornegin Faz 4 ve Faz 5 bagimsiz calisilabilir).
