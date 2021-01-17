import time

from common.scene import Scene
from common.tool import load_resource
from games.azurelane.assist import calculate_move_map


def difficult_small(prefix):
    return Scene('检测中型舰队标志',
                 identify_image=load_resource("difficult_medium.png", prefix),
                 tap_offset_x=40, tap_offset_y=30, threshold=0.7)


def difficult_medium(prefix):
    return Scene('检测中型舰队标志',
                 identify_image=load_resource("difficult_medium.png", prefix),
                 tap_offset_x=40, tap_offset_y=30, threshold=0.7)


def difficult_large(prefix):
    return Scene('检测中型舰队标志',
                 identify_image=load_resource("difficult_medium.png", prefix),
                 tap_offset_x=40, tap_offset_y=30, threshold=0.7)


def map_move_spec_question_mark(prefix):
    return Scene('检测问号探索点',
                 identify_image=load_resource("explore_map_question_mark.png", prefix),
                 tap_offset_y=50)


def load_boss_ship_features(prefix):
    return [
        Scene("检测旗舰", identify_image=load_resource("boss_icon_detection2.png", prefix), threshold=0.7),
        Scene("检测旗舰（带人物）", identify_image=load_resource("boss_small.png", prefix), threshold=0.7),
        Scene("检测旗舰2（带人物）", identify_image=load_resource("boss_small2.png", prefix), threshold=0.7),
    ]


def load_fish_ship_features(prefix):
    return [
        map_move_spec_question_mark(prefix),
        Scene("检测侦查舰队", identify_image=load_resource("map_ship_type_1.png", prefix)),  # 判断
        Scene("检测航母舰队", identify_image=load_resource("map_ship_type_2.png", prefix)),  # 判断航母舰队
        Scene("检测主力舰队", identify_image=load_resource("map_ship_type_3.png", prefix)),  # 判断主力舰队
        Scene("检测运输舰队", identify_image=load_resource("map_ship_type_4.png", prefix)),  # 判断侦查舰队
        Scene("检测舰队等级", identify_image=load_resource("enemy_level.png", prefix), threshold=0.6, tap_offset_y=-55),
        difficult_small(prefix),  # 小型舰队
        difficult_medium(prefix), # 中型舰队
        difficult_large(prefix),  # 大型舰队
    ]


class EnemySearch(Scene):
    context = None
    config = None
    boss_features = []
    fish_features = []
    red_zones = [
        ((0, 0), (108, 640)),       # 左侧队伍预览
        ((108, 0), (1062, 53)),     # 顶部信息栏(石油、金币、钻石)
        ((108, 53), (783, 96)),     # 舰队编号、制空值
        ((108, 96), (347, 141)),    # 舰队属性(小图标、指挥喵加成)
        ((108, 141), (347, 256)),   # 7-2地图左上角容易引发不可达路径的禁区
        ((1062, 0), (1136, 65)),    # 
        ((1090, 88), (1136, 195)),  # 星级预览
        ((1046, 358), (1136, 472)), # 损管、阵型切换
        ((580, 557), (1136, 640)),  # 撤退、切换、迎击按钮
    ]
    tap_x = -1
    tap_y = -1

    def __init__(self, name, identify_image, context, config, prefix):
        super().__init__(name, identify_image)
        self.fish_features = load_fish_ship_features(prefix + 'search_ship_feature/')
        self.boss_features = load_boss_ship_features(prefix + 'search_ship_feature/')
        self.context = context
        self.config = config
        self.swich_team_btn = Scene('切换队伍按钮',
                                    identify_image=load_resource("switch_team.png",
                                                                 prefix=prefix + '/scenes_feature/' + config.language + '/'))

    def before_action(self, device, screen):
        if self.config.team_switch and \
                not self.context.team_switched and \
                self.context.round_count >= self.config.team_switch_threshold:
            x, y = self.swich_team_btn.where_to_tap(screen)
            device.tap_handler(x, y)
            self.context.team_switched = True
            print('更换队伍,', end='')
            self.type = 'wait'
            return

        if self.context.team_switched:
            features = self.boss_features
        else:
            features = self.fish_features

        for i in range(len(features)):
            feature = features[i]
            possible_targets = feature.matched_in(screen)
            if len(possible_targets) > 0:
                for j in range(len(possible_targets)):
                    # x, y = feature.where_to_tap(screen)
                    x, y = possible_targets[j][0], possible_targets[j][1]
                    x += feature.tap_offset_x
                    y += feature.tap_offset_y
                    if self.__check_in_red_zone(x, y):
                        continue
                    else:
                        self.type = 'tap'
                        self.tap_x = x
                        self.tap_y = y
                        return
        self.type = 'swipe'

    def where_to_tap(self, screen):
        return self.tap_x, self.tap_y

    def after_action(self, device, screen):
        if self.type == 'tap':
            # 点击后，预留10s的时间，等待舰队移动到目标点，
            # 避免到达目标点前截图，载入队伍阵型界面时触发了手势滑动操作，改变阵型
            time.sleep(5)

    def how_to_swipe(self):
        return calculate_move_map(self.context, self.config)

    def __check_in_red_zone(self, tap_x, tap_y):
        for i in range(len(self.red_zones)):
            zone = self.red_zones[i]
            rect_left_top = zone[0]
            rect_right_bottom = zone[1]
            if rect_left_top[0] <= tap_x <= rect_right_bottom[0] and rect_left_top[1] <= tap_y <= rect_right_bottom[1]:
                return True
        return False
