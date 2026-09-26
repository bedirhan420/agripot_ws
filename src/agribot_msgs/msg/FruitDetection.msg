# Tek bir meyve algilamasi (perception -> navigation/manipulation)
std_msgs/Header header

string track_id
string fruit_type
uint8 maturity_level
uint8 MATURITY_UNKNOWN=0
uint8 MATURITY_UNRIPE=1
uint8 MATURITY_RIPENING=2
uint8 MATURITY_RIPE=3
uint8 MATURITY_OVERRIPE=4

float32 confidence

# 2D goruntu duzlemi bilgisi (debug/gorsellestirme icin)
float32 bbox_x_min
float32 bbox_y_min
float32 bbox_x_max
float32 bbox_y_max

# 3D konum (derinlik verisinden hesaplanir), header.frame_id cercevesinde
geometry_msgs/PoseStamped pose_3d
bool has_3d_pose
