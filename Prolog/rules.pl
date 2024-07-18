% 定义合法状态的规则

% Rule 灯泡打开的时候，没有按下开关，插座打开，电压高，传感器高传感
valid_state(bulb_on, switch_unpressed, socket_on, high_voltage, sensor_high).

% Rule 灯泡关闭的时候，没有按下开关，插座关闭，电压低，传感器低传感
valid_state(bulb_off, switch_unpressed, socket_off, low_voltage, sensor_low).

% Rules 开关被按下的时候，用户在干涉设备，不考虑其他因素
valid_state(_, switch_pressed, _, _, _).

% 用户查询接口
is_valid_state(Bulb, Switch, Socket, Voltage, Sensor) :-
    (   valid_state(Bulb, Switch, Socket, Voltage, Sensor)
    ->  write('true'), nl   % 如果匹配规则，输出 true 并换行
    ;   write('false'), nl  % 如果不匹配规则，输出 false 并换行
    ).

% 程序初始化和退出控制
:- initialization(main).
main :-
    current_prolog_flag(argv, Arguments),
    run(Arguments),
    halt.

% 解析命令行参数并调用 is_valid_state
run([Bulb, Switch, Socket, Voltage, Sensor]) :-
    is_valid_state(Bulb, Switch, Socket, Voltage, Sensor).
