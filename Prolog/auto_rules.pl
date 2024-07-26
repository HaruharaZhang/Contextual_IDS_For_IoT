% valid_state 应该接收一个参数列表并检查这个状态是否有效
% valid_state([H1, H2, H3, H4, H5, H6, H7, H8, H9, H10, H11, H12, H13, H14, H15, H16, H17, H18, H19, H20, H21, H22, H23, H24, H25, H26, H27, H28, H29, H30, H31, H32, H33, H34, H35, H36, H37]) :-

is_valid_state(ArgsList) :-
    valid_state(ArgsList) -> write('True'); write('False').

:- initialization(main).
main :-
    current_prolog_flag(argv, Arguments),
    run(Arguments),
    halt.

% 解析命令行参数并调用 is_valid_state
run(Arguments) :-
    is_valid_state(Arguments).

% 程序自定义添加规则
valid_state('3:12:59df-2b71-4f01-8343', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '254', 'True', '00:17:88:01:09:a0:43:42-0b', '1002', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'False', '0', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '0', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_normal, ''temputer_sensor_normal').
valid_state('3:12:59df-2b71-4f01-8343', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '254', 'True', '00:17:88:01:09:a0:43:42-0b', '1002', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'False', '0', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '0', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_high, ''temputer_sensor_normal').
valid_state('3:12:59df-2b71-4f01-8343', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '254', 'True', '00:17:88:01:09:a0:43:42-0b', '1002', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'False', '0', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '0', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_high, ''temputer_sensor_high').
