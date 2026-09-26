# AgriBot - Mimari Dokumani

## 1. Genel Bakis

AgriBot, tek bir ROS2 workspace icinde **6 paket** olarak organize edilmis
katmanli bir mimariye sahiptir. Katmanlar arasindaki bagimlilik yonu
**her zaman disariya (soyutlamaya) dogrudur** (Dependency Inversion
Principle): ust seviye moduller (`agribot_navigation`, `agribot_manipulation`,
`agribot_perception`) somut siniflara degil, `agribot_core` icindeki
arayuzlere (interfaces) bagimlidir.

```
                        +-------------------+
                        |   agribot_core    |   <-- interfaces + ortak tipler
                        | (framework-free)  |       (hicbir seye bagimli degil)
                        +---------+---------+
                                  ^
            +---------------------+---------------------+
            |                     |                      |
  +---------+--------+  +---------+---------+  +---------+-----------+
  | agribot_perception|  | agribot_navigation|  | agribot_manipulation|
  |  (YOLOv8, olgunluk)|  | (sira takibi,EKF, |  |  (MoveIt2, kuvvet,  |
  |                    |  |  State/Strategy)  |  |   Command Pattern)  |
  +---------+----------+  +---------+---------+  +----------+----------+
            |                       |                        |
            +-----------+-----------+------------------------+
                        |
                +-------+--------+        +--------------------+
                | agribot_msgs   |        | agribot_simulation |
                | (ROS2 arayuz)  |        | (Gazebo/MuJoCo,    |
                +----------------+        |  breakable joint,  |
                                            |  dinamik engeller) |
                                            +----------+---------+
                                                       |
                                            +----------+---------+
                                            | agribot_description|
                                            |  (URDF/Xacro)      |
                                            +--------------------+

                    Hepsi agribot_bringup uzerinden orkestre edilir.
```

## 2. Veri Akisi (uctan uca bir hasat dongusu)

1. `agribot_simulation`: Gazebo, RGB-D + IMU + GPS verisini ros_gz_bridge
   uzerinden ROS2 topic'lerine yayinlar.
2. `agribot_perception/perception_node`: RGB-D senkronize edilir, YOLOv8
   ile meyve tespit edilir, HSV tabanli olgunluk sinifi atanir,
   `/agribot/perception/detections` (`FruitDetectionArray`) yayinlanir.
3. `agribot_navigation/navigation_manager_node`: nokta bulutunu
   `RowDetector`'a verir, `MissionContext` (State Pattern) tetiklenir:
   - Varsayilan durum `RowFollowingState` -> `RowFollowingStrategy` PD
     kontrolcusu ile `/cmd_vel` uretir.
   - Olgun bir meyve algilanip ulasilabilir oldugunda ->
     `ApproachingFruitState` -> `HarvestingState`.
   - Dinamik engel algilandiginda -> `ObstacleAvoidanceState` ->
     `ObstacleAvoidanceStrategy` (Nav2 costmap+local planner devreye girer).
4. `HarvestingState.on_enter`, `agribot_manipulation`'daki `HarvestFruit`
   action sunucusuna hedefi gonderir.
5. `ManipulationNode`: `HarvestPlannerFactory` ile `AppleHarvestPlanner`
   olusturur, bunu bir `HarvestFruitCommand`'a sarar, `CommandInvoker`
   uzerinden calistirir. Plan MoveIt2 (`MoveIt2Adapter`) ile yurutulur,
   kopma kuvveti `ForceController` ile uygulanir.
6. Hedef kuvvete ulasilinca, `agribot_simulation/scripts/breakable_joint_manager.py`
   ilgili `apple_fruit` modelinin `DetachableJoint` eklentisine sinyal
   gonderir; meyve fiziksel olarak agactan kopar.
7. Sonuc `HarvestStatus`/action-result olarak geri bildirilir,
   `MissionContext` `RowFollowingState`'e doner.

## 3. Navigasyon Katmaninin Tasarim Gerekcesi

Proje dokumaninin temel vurgusu, **2D Lidar SLAM'in yetersiz kaldigi
duvarsiz tarim ortamlarinda** RGB-D + 3D point cloud tabanli sira takibi
yapmaktir. Bu nedenle mimari BILINCLI olarak iki ayri sorumluluk ayirir:

| Gorev                                   | Sorumlu bilesen                              |
|------------------------------------------|-----------------------------------------------|
| Sira ici hassas merkezleme (surekli)      | `RowFollowingStrategy` (custom, point-cloud)  |
| Sira donusu / satirlar arasi manevra      | `WaypointStrategy` (Nav2 `NavigateToPose`)    |
| Dinamik engel kacinma (traktor/isci/hayvan)| `ObstacleAvoidanceStrategy` (Nav2 costmap)    |

Nav2'nin **genel amacli local planner'i bilerek KUCUK bir role indirgenmistir**:
yalnizca dinamik engellerde ve donuslerde kullanilir; GPS de proje
dokumaninda vurgulandigi gibi "her zaman guvenilir degildir" varsayimiyla
EKF'de ikincil bir kaynak olarak ele alinir (bkz. `ekf_params.yaml`).

## 4. Simulasyon Backend Secimi (Gazebo vs MuJoCo)

`ISimulationBackend` arayuzu (Adapter Pattern) sayesinde proje HER IKI
motoru da destekleyecek sekilde tasarlanmistir:

- **GazeboSimBackend**: `gz-sim`'in native `DetachableJoint` sistem
  eklentisini kullanir (gercek, mevcut bir Gazebo ozelligi). Zemin
  surtunmesi (mu1/mu2) SDF'de statiktir; runtime degisimi icin "camur
  patch'i spawn etme" stratejisi kullanilir (bkz. `mud_friction_randomizer.py`).
- **MuJoCoSimBackend**: MuJoCo'nun `equality`/`weld` kisitlarini
  "kirilabilir eklem" olarak kullanir; zemin surtunmesi (`geom friction`)
  Gazebo'nun aksine RUNTIME'DA degistirilebilir (MuJoCo'nun avantaji).
  Ancak `break_joint()` icin mujoco_ros koprusune `/mujoco/set_equality_active`
  adinda KUCUK bir ozel servis eklemeniz gerekir; varsayilan koprude bu yoktur
  (bkz. ROADMAP Faz 6, "MuJoCo custom servis" gorevi).

Baslangicta **Gazebo (Ignition) onerilir** (kullanicinin mesajinda da
belirtildigi gibi native DetachableJoint hazir oldugu icin daha az ozel
gelistirme gerektirir); MuJoCo, kontak dinamiklerinin daha kritik oldugu
(ornegin quadruped tecrubesine dayanan camur-tekerlek etkilesimi ince
ayari) ileri fazlarda devreye alinabilir.

## 5. Katmanlar Arasi Bagimliliklar (paket seviyesinde)

```
agribot_msgs        <- (bagimsiz, sadece rosidl)
agribot_core         <- rclpy (minimal)
agribot_perception    <- agribot_core, agribot_msgs
agribot_navigation    <- agribot_core, agribot_msgs
agribot_manipulation  <- agribot_core, agribot_msgs
agribot_description   <- (bagimsiz, URDF/Xacro)
agribot_simulation    <- agribot_core, agribot_msgs, agribot_description (worlds spawn eder)
agribot_bringup       <- hepsi (yalnizca launch/config, kod YOK)
```

`agribot_bringup` KASITLI OLARAK hicbir is-mantigi kodu icermez; yalnizca
diger paketleri "kablolamaktan" (wiring) sorumludur. Bu, sistemin
herhangi bir alt kumesinin (ornegin yalnizca perception + simulation)
bagimsiz test edilebilmesini saglar.
