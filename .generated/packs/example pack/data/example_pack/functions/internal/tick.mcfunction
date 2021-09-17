#This function is run every tick after this datapack is loaded.

#Run listeners
execute as @e[scores={used_c_stick=1..}] at @s run function example_pack:listeners/used_carrot_on_a_stick/main/used_carrot_on_a_stick1

#Reset listener scores
scoreboard players set @e used_c_stick 0

#Run tick listeners
function example_pack:listeners/tick/test/tick2
function example_pack:listeners/tick/main/tick1
tag @e[tag=!example_pack_spawned] add example_pack_spawned

#Start the tick function again next tick
schedule function example_pack:internal/tick 1t replace