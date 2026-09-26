# AgriBot - Tasarim Deseni Katalogu

Her desen; **nerede kullanildigi**, **hangi SOLID ilkesini desteklendigi**
ve **neden bu deseni sectigimiz** ile birlikte listelenmistir.

| # | Desen | Konum (dosya/sinif) | SOLID Ilkesi | Gerekce |
|---|-------|----------------------|---------------|---------|
| 1 | **Strategy** | `agribot_core/interfaces/i_navigation_strategy.py` + `agribot_navigation/strategies/*` (RowFollowing, Waypoint, ObstacleAvoidance) | OCP, DIP | Sira takibi / donus / engel-kacinma algoritmalari birbirinden BAGIMSIZ gelisir; yeni bir strateji (ornegin "TerraceStrategy" egimli arazi icin) eklemek icin mevcut kod DEGISMEZ. |
| 2 | **Strategy** | `agribot_perception/detectors/base_detector.py` (`IDetector`) | LSP, ISP | `YOLOv8Detector` yerine gelecekte bir segmentasyon modeli sorunsuzca takilabilir. |
| 3 | **State** | `agribot_navigation/state_machine/*` (`IRobotState`, `RowFollowingState`, `HarvestingState`, ...) | SRP, OCP | Gorev akisinin (idle->navigasyon->yaklasma->hasat->...) her adimi kendi sinifinda yasar; dev bir if/elif zincirinden kacinilir. |
| 4 | **Factory Method** | `DetectorFactory`, `NavigationStrategyFactory`, `HarvestPlannerFactory`, `ObstacleFactory` | OCP, DIP | Cagiran kod ("hangi detektor/strateji/planlayici") somut sinif ismini BILMEZ; yalnizca bir anahtar string (ROS2 parametresinden) verir. |
| 5 | **Adapter** | `agribot_core/interfaces/i_simulation_backend.py` + `agribot_simulation/backends/{gazebo_backend,mujoco_backend}.py` | LSP, DIP | Gazebo ve MuJoCo'nun COK FARKLI API'leri, ortak bir sozlesme (`ISimulationBackend`) altina alinir; ust kod motor degisikliginden ETKILENMEZ. |
| 6 | **Adapter / Facade** | `agribot_manipulation/planning/moveit2_adapter.py` (`MoveIt2Adapter`) | DIP, SRP | MoveIt2'nin genis API'si (`MoveItPy`, planning scene, IK cozucu) tek bir basit arayuze indirgenir. |
| 7 | **Template Method** | `agribot_manipulation/planning/harvest_planner.py` (`HarvestPlanner.execute_harvest`) | OCP | Hasat surecinin SABIT adim sirasi (yaklas->hizala->kavra->kuvvet uygula->dogrula->geri cek) korunurken, meyve-turune-ozgu adimlar (`AppleHarvestPlanner`) override edilir. |
| 8 | **Command** | `agribot_core/interfaces/i_harvest_command.py`, `agribot_manipulation/commands/{harvest_command,command_invoker}.py` | SRP | Her hasat girisimi bir nesneye donusur; kuyruklama, yeniden deneme (retry) ve `undo()` ile guvenli geri cekilme merkezi bir `CommandInvoker`'da yonetilir. |
| 9 | **Observer** | `agribot_core/interfaces/observer.py` (`Subject`/`IObserver`), `PerceptionNode` (Subject olarak) | OCP, SRP | Yeni bir "algilama dinleyicisi" (ornegin telemetri kaydedici) eklemek icin `PerceptionNode` DEGISMEZ. |
| 10 | **Singleton** (bilincli, sinirli) | `agribot_core/config/config_manager.py` (`ConfigManager`) | -- (bilerek DI'a istisna) | YALNIZCA salt-okunur, statik konfigurasyon icin; degistirilemez (frozen) API ve `reset_for_testing()` ile test izolasyonu saglanir. Mutable/paylasimli durum ASLA burada tutulmaz. |

## Bilincli Olarak Kullanilmayan/Sinirlandirilan Desenler

- **Singleton (genel amacli)**: Projede varsayilan yaklasim Dependency
  Injection'dir (her sinif bagimliliklarini constructor'dan alir). Bunun
  tek istisnasi yukarida gerekcelendirilen `ConfigManager`'dir.
- **Inheritance-agirlikli hiyerarsiler**: Ozellikle `strategies/` ve
  `commands/` altinda **kompozisyon miras'a tercih edilmistir**
  (ornegin `MissionContext`, bir `INavigationStrategy` miras almaz,
  onu bir alan olarak TUTAR). Bu, calisirken strateji degistirmeyi
  (runtime polymorphism) miras agaci degistirmeden mumkun kilar.

## SOLID Ilkelerinin Ozet Haritasi

- **S**ingle Responsibility: her node/sinif TEK bir sey yapar (ornegin
  `RowDetector` yalnizca geometri hesaplar, kontrol komutu URETMEZ --
  bu `RowFollowingStrategy`'nin isidir).
- **O**pen/Closed: Factory + Strategy sayesinde yeni davranis EKLEMEK
  icin mevcut siniflar DEGISTIRILMEZ.
- **L**iskov Substitution: `IDetector`, `INavigationStrategy`,
  `ISimulationBackend` implementasyonlari birbirinin YERINE gecebilir.
- **I**nterface Segregation: arayuzler KUCUK ve odaklidir (`IHarvestCommand`
  yalnizca `execute/undo/describe`; dev bir "IRobot" arayuzu YOKTUR).
- **D**ependency Inversion: `agribot_navigation`/`agribot_manipulation`/
  `agribot_perception`, `agribot_core`'daki SOYUTLAMALARA bagimlidir,
  birbirlerinin SOMUT siniflarina degil.
