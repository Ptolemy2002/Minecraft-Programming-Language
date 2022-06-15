#This function is run when the datapack is loaded.
scoreboard objectives add ep_temp dummy
scoreboard players set example_pack ep_temp 0

#Used for listener used:carrot_on_a_stick
scoreboard objectives add used_c_stick used:carrot_on_a_stick

#Run listeners
function example_pack:listeners/load/main/load1

#Uninstall if incompatible
execute if data storage example_pack {isCompatible:1} run tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]
#Uninstall the pack if it is incompatible
execute if data storage example_pack {isCompatible:0} run function example_pack:uninstall

#Start the tick function
execute if score example_pack ep_temp matches 1 run function example_pack:internal/tick