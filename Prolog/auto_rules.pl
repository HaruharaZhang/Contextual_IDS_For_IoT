
%:- initialization(main).

main :-
    current_prolog_flag(argv, Arguments),
    run(Arguments),
    halt.

run(Arguments) :-
    is_valid_state(Arguments).

% 定义 is_valid_state/1，调用 valid_state/35
is_valid_state(ArgsList) :-
    length(ArgsList, 35), % 确保参数数量为36
    (   valid_state(ArgsList)
    ->  write('True')
    ;   write('False')
    ).

% 定义 valid_state/36
%swipl -s /home/msc-lab/Contextual_IDS_For_IoT/Prolog/auto_rules.pl -g "is_valid_state(['True', 'True', '158', 'True', '00:17:88:01:09:a0:43:42-0b', '1003', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'True', '1', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_high', 'temputer_sensor_high']),halt."
%swipl -s /home/msc-lab/Contextual_IDS_For_IoT/Prolog/auto_rules.pl -g "is_valid_state(['True', 'True', '158', 'True', '00:17:88:01:09:a0:43:42-0b', '1003', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'True', '1', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_high', 'temputer_sensor_high']),halt."


valid_state(['True', '254', 'True', '00:17:88:01:09:a0:43:42-0b', '1002', 'switch_unpressed', '2:9:a8e4-3154-4245-a71c', 'True', 'True', 'False', '2:10:949a-5b37-4cb8-b853', 'True', 'True', 'False', '0:11:fc98-6706-4a72-aed7', 'True', 'True', 'False', '3:12:59df-2b71-4f01-8343', 'True', 'True', 'False', '80067C280DF5CE62418BAFEC45D2B4BA22324F60', 'True', '1', 'True', '8006F5E0647258387C88F44F3BD425751FB882D8', '8006F5E0647258387C88F44F3BD425751FB882D800', '1', '8006F5E0647258387C88F44F3BD425751FB882D801', '1', '8006F5E0647258387C88F44F3BD425751FB882D802', '1', 'light_sensor_high', 'temputer_sensor_high']).
