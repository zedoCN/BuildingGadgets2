#!/usr/bin/env python3
"""Exercise the real AE2 grid through an isolated integrated client (see README)."""
import json, pathlib, time, urllib.request
ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'runs/client/config/mcpfabric.config.json').read_text())
REPORT = []
IMPORTS = ['java.util.*', 'java.util.concurrent.TimeUnit', 'net.minecraft.server.MinecraftServer',
 'net.minecraft.core.*', 'net.minecraft.world.item.*', 'net.minecraft.world.level.block.Blocks',
 'net.minecraft.world.level.material.Fluids', 'net.minecraft.network.chat.Component',
 'com.direwolf20.buildinggadgets2.util.*', 'com.direwolf20.buildinggadgets2.setup.*',
 'com.direwolf20.buildinggadgets2.common.items.*', 'com.direwolf20.buildinggadgets2.util.datatypes.StatePos',
 'appeng.api.features.*', 'appeng.api.config.Actionable', 'appeng.api.networking.security.IActionSource',
 'appeng.api.stacks.*', 'appeng.core.definitions.*', 'appeng.blockentity.storage.DriveBlockEntity',
 'appeng.blockentity.networking.WirelessAccessPointBlockEntity', 'net.neoforged.neoforge.fluids.FluidStack']
def rpc(method, params=None):
 req=urllib.request.Request(f'http://127.0.0.1:{CFG["port"]}/rpc',data=json.dumps({'method':method,'params':params or {}}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+CFG['token']})
 with urllib.request.urlopen(req,timeout=35) as response: result=json.load(response)
 if not result.get('ok'): raise RuntimeError(result)
 return result['result']
def server(body):
 code='''var server=(MinecraftServer)ctx.server();
 if(server==null || !server.isSingleplayer() || !server.getWorldPath(net.minecraft.world.level.storage.LevelResource.ROOT).normalize().endsWith("AE2Verification")) throw new IllegalStateException("Isolated AE2Verification world required");
 return server.submit(() -> {var level=server.overworld();var player=server.getPlayerList().getPlayers().getFirst();
 '''+body+'''}).get(20,TimeUnit.SECONDS);'''
 return rpc('unsafe.javaScratch',{'imports':IMPORTS,'body':code,'mainThread':False})['result']
def check(name, body):
 result=server(body)
 if result is not True: raise AssertionError((name,result))
 REPORT.append(name); print('PASS',name,flush=True)
def pause(): time.sleep(2)

GRID = """var pos=GlobalPos.of(level.dimension(),new BlockPos(0,65,-1));
 var ap=(WirelessAccessPointBlockEntity)level.getBlockEntity(pos.pos());
 var storage=ap.getGrid().getStorageService().getInventory();var source=IActionSource.ofPlayer(player);
 var stone=AEItemKey.of(Items.STONE);var water=AEFluidKey.of(Fluids.WATER);
 """
def gridcheck(name,body): check(name,GRID+body)

def main():
 rpc('screen.close')
 print(server('''
 player.setGameMode(net.minecraft.world.level.GameType.CREATIVE);
 player.getInventory().clearContent();
 for (var pos:BlockPos.betweenClosed(-3,65,-3,3,68,3)) level.setBlockAndUpdate(pos,Blocks.AIR.defaultBlockState());
 level.setBlockAndUpdate(new BlockPos(0,65,0),AEBlocks.DRIVE.block().defaultBlockState().setValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.FACING,Direction.EAST));
 level.setBlockAndUpdate(new BlockPos(-1,65,0),AEBlocks.CREATIVE_ENERGY_CELL.block().defaultBlockState());
 level.setBlockAndUpdate(new BlockPos(0,65,-1),AEBlocks.WIRELESS_ACCESS_POINT.block().defaultBlockState());
 var drive=(DriveBlockEntity)level.getBlockEntity(new BlockPos(0,65,0));
 drive.getInternalInventory().setItemDirect(0,AEItems.ITEM_CELL_1K.stack());
 drive.getInternalInventory().setItemDirect(1,AEItems.FLUID_CELL_1K.stack());
 return "grid created";'''))
 pause()
 check('three gadget types register with AE2', '''for(var item:List.of(Registration.Building_Gadget.get(),Registration.Exchanging_Gadget.get(),Registration.CopyPaste_Gadget.get())) if(GridLinkables.get(item)==null)return false;return GridLinkables.get(Registration.CutPaste_Gadget.get())==null;''')
 check('real wireless access point online', '''var ap=(WirelessAccessPointBlockEntity)level.getBlockEntity(new BlockPos(0,65,-1));return ap.isActive() && ap.getGrid()!=null;''')
 check('bind and unlink all three gadgets', '''var pos=GlobalPos.of(level.dimension(),new BlockPos(0,65,-1));for(var item:List.of(Registration.Building_Gadget.get(),Registration.Exchanging_Gadget.get(),Registration.CopyPaste_Gadget.get())){var stack=new ItemStack(item);var handler=GridLinkables.get(item);if(!handler.canLink(stack))return false;handler.link(stack,pos);if(!pos.equals(GadgetNBT.getBoundPos(stack)))return false;handler.unlink(stack);if(GadgetNBT.getBoundPos(stack)!=null)return false;}return true;''')
 gridcheck('seed real storage cells', 'return storage.insert(stone,64,Actionable.MODULATE,source)==64 && storage.insert(water,2000,Actionable.MODULATE,source)==2000;')
 gridcheck('item previews never consume stock', '''for(int i=0;i<20;i++){if(!BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE,2)),true,pos,Direction.NORTH))return false;}return storage.getAvailableStacks().get(stone)==64;''')
 gridcheck('insufficient item request consumes nothing', '''return !BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE,65)),false,pos,Direction.NORTH) && storage.getAvailableStacks().get(stone)==64;''')
 gridcheck('item components must match', '''var named=new ItemStack(Items.STONE);named.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,Component.literal("different"));return !BuildingUtils.removeStacksFromInventory(player,List.of(named),false,pos,Direction.NORTH) && storage.getAvailableStacks().get(stone)==64;''')
 gridcheck('actual item extraction', '''return BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE,2)),false,pos,Direction.NORTH) && storage.getAvailableStacks().get(stone)==62;''')
 gridcheck('item return enters bound network', '''BuildingUtils.giveItemToPlayer(player,new ItemStack(Items.STONE,2),pos,Direction.NORTH);return storage.getAvailableStacks().get(stone)==64 && player.getInventory().countItem(Items.STONE)==0;''')
 gridcheck('fluid previews never consume stock', '''for(int i=0;i<20;i++){var need=new FluidStack(Fluids.WATER,1000);if(!BuildingUtils.removeFluidStacksFromInventory(player,need,true,pos,Direction.NORTH) || !need.isEmpty())return false;}return storage.getAvailableStacks().get(water)==2000;''')
 gridcheck('insufficient fluid request consumes nothing', '''var need=new FluidStack(Fluids.WATER,3000);return !BuildingUtils.removeFluidStacksFromInventory(player,need,false,pos,Direction.NORTH) && need.getAmount()==3000 && storage.getAvailableStacks().get(water)==2000;''')
 gridcheck('actual fluid extraction and return', '''var need=new FluidStack(Fluids.WATER,1000);if(!BuildingUtils.removeFluidStacksFromInventory(player,need,false,pos,Direction.NORTH) || storage.getAvailableStacks().get(water)!=1000)return false;var returned=new FluidStack(Fluids.WATER,1000);BuildingUtils.giveFluidToPlayer(player,returned,pos,Direction.NORTH);return returned.isEmpty() && storage.getAvailableStacks().get(water)==2000;''')
 gridcheck('full fluid cell retains unaccepted remainder', '''storage.insert(water,1000000000,Actionable.MODULATE,source);storage.extract(water,500,Actionable.MODULATE,source);var returned=new FluidStack(Fluids.WATER,1000);com.direwolf20.buildinggadgets2.integration.AE2Methods.insertFluidIntoAE2(player,pos,returned);return returned.getAmount()==500;''')
 gridcheck('full item cell retains unaccepted remainder', '''storage.insert(stone,1000000000,Actionable.MODULATE,source);storage.extract(stone,2,Actionable.MODULATE,source);var returned=new ItemStack(Items.STONE,5);com.direwolf20.buildinggadgets2.integration.AE2Methods.insertIntoAE2(player,pos,returned);return returned.getCount()==3;''')
 gridcheck('prepare survival build using only ME materials', '''storage.extract(stone,1000000000,Actionable.MODULATE,source);storage.insert(stone,64,Actionable.MODULATE,source);player.getInventory().clearContent();var gadget=new ItemStack(Registration.Building_Gadget.get());gadget.set(BG2DataComponents.FORGE_ENERGY.get(),100000);GadgetNBT.setRenderType(gadget,(byte)0);GridLinkables.get(gadget.getItem()).link(gadget,pos);player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gadget);player.setGameMode(net.minecraft.world.level.GameType.SURVIVAL);var target=new BlockPos(12,65,0);level.setBlockAndUpdate(target,Blocks.AIR.defaultBlockState());var list=new ArrayList<StatePos>(List.of(new StatePos(Blocks.STONE.defaultBlockState(),BlockPos.ZERO)));var id=BuildingUtils.build(level,player,list,target,gadget,true);GadgetUtils.addToUndoList(level,gadget,new ArrayList<>(),id);return true;''')
 pause()
 gridcheck('survival build places block and consumes exactly one ME item', '''return level.getBlockState(new BlockPos(12,65,0)).is(Blocks.STONE) && storage.getAvailableStacks().get(stone)==63 && player.getInventory().countItem(Items.STONE)==0;''')
 gridcheck('schedule real gadget undo', '''var gadget=player.getMainHandItem();((BaseGadget)gadget.getItem()).undo(level,player,gadget);return true;''')
 pause()
 gridcheck('undo removes block and returns exactly one ME item', '''return level.getBlockState(new BlockPos(12,65,0)).isAir() && storage.getAvailableStacks().get(stone)==64 && player.getInventory().countItem(Items.STONE)==0;''')
 check('prepare distant building and quantum cut fixture', '''player.setGameMode(net.minecraft.world.level.GameType.CREATIVE);level.setChunkForced(0,0,true);level.setChunkForced(0,-1,true);player.teleportTo(100.5,65,0.5);return true;''')
 pause()
 gridcheck('ME materials remain accessible beyond wireless range', '''return player.distanceToSqr(0.5,65,-0.5)>ap.getRange()*ap.getRange() && BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE)),true,pos,Direction.NORTH);''')
 check('prepare quantum ring relocation', '''player.teleportTo(10.5,65,8.5);var a=new BlockPos(10,65,10);level.setBlockAndUpdate(a,AEBlocks.QUANTUM_RING.block().defaultBlockState());var tool=new ItemStack(Registration.CutPaste_Gadget.get());player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,tool);GadgetNBT.setRenderType(tool,(byte)0);GadgetNBT.setCopyStartPos(tool,a);GadgetNBT.setCopyEndPos(tool,a);((GadgetCutPaste)tool.getItem()).cutAndStore(player,tool);return true;''')
 pause()
 check('quantum ring cut retains state and block entity', '''var tool=player.getMainHandItem();var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);var id=GadgetNBT.getUUID(tool);return level.getBlockState(new BlockPos(10,65,10)).isAir() && data.getCopyPasteList(id,false).stream().anyMatch(s -> s.state.is(AEBlocks.QUANTUM_RING.block())) && !data.peekTEMap(id).isEmpty();''')
 check('schedule quantum ring paste', '''var tool=player.getMainHandItem();var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);var id=GadgetNBT.getUUID(tool);level.setBlockAndUpdate(new BlockPos(12,65,10),Blocks.AIR.defaultBlockState());BuildingUtils.buildWithTileData(level,player,data.getCopyPasteList(id,false),new BlockPos(12,65,10),data.peekTEMap(id),tool);return true;''')
 pause()
 check('quantum ring pastes once with block entity', '''var p=new BlockPos(12,65,10);return level.getBlockState(p).is(AEBlocks.QUANTUM_RING.block()) && level.getBlockEntity(p) instanceof appeng.blockentity.qnb.QuantumBridgeBlockEntity;''')
 check('cut-paste replacement defaults off without mutating saved settings', '''var tool=new ItemStack(Registration.CutPaste_Gadget.get());if(GadgetNBT.getPasteReplace(tool) || tool.has(BG2DataComponents.SETTING_TOGGLES.get(GadgetNBT.ToggleableSettings.PASTE_REPLACE)))return false;tool.set(BG2DataComponents.SETTING_TOGGLES.get(GadgetNBT.ToggleableSettings.PASTE_REPLACE),true);if(!GadgetNBT.getPasteReplace(tool))return false;tool.set(BG2DataComponents.SETTING_TOGGLES.get(GadgetNBT.ToggleableSettings.PASTE_REPLACE),false);return !GadgetNBT.getPasteReplace(tool);''')
 check('prepare blocked paste with genuine cut contents', '''var a=new BlockPos(10,65,12);level.setBlockAndUpdate(a,Blocks.STONE.defaultBlockState());var tool=new ItemStack(Registration.CutPaste_Gadget.get());player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,tool);GadgetNBT.setRenderType(tool,(byte)0);GadgetNBT.setCopyStartPos(tool,a);GadgetNBT.setCopyEndPos(tool,a);((GadgetCutPaste)tool.getItem()).cutAndStore(player,tool);return true;''')
 pause()
 check('blocked paste keeps quantum ring and clipboard', '''var tool=player.getMainHandItem();GadgetNBT.setMode(tool,new com.direwolf20.buildinggadgets2.util.modes.Paste());GadgetNBT.setAnchorPos(tool,new BlockPos(12,64,10));((BaseGadget)tool.getItem()).use(level,player,net.minecraft.world.InteractionHand.MAIN_HAND);var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);var list=data.getCopyPasteList(GadgetNBT.getUUID(tool),false);return level.getBlockState(new BlockPos(12,65,10)).is(AEBlocks.QUANTUM_RING.block()) && list!=null && list.stream().anyMatch(q->q.state.is(Blocks.STONE)) && GadgetNBT.getMode(tool).getId().getPath().equals("paste") && GadgetNBT.hasCopyUUID(tool);''')
 check('retry preserved clipboard at empty destination', '''var tool=player.getMainHandItem();level.setBlockAndUpdate(new BlockPos(14,65,10),Blocks.AIR.defaultBlockState());GadgetNBT.setAnchorPos(tool,new BlockPos(14,64,10));((BaseGadget)tool.getItem()).use(level,player,net.minecraft.world.InteractionHand.MAIN_HAND);return true;''')
 pause()
 check('successful retry places once and stale undo is harmless', '''var tool=player.getMainHandItem();var item=(BaseGadget)tool.getItem();item.undo(level,player,tool);var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);return level.getBlockState(new BlockPos(14,65,10)).is(Blocks.STONE) && !item.canUndo(level,player,tool) && data.getCopyPasteList(GadgetNBT.getUUID(tool),false)==null;''')
 # Exercise actual client/server menu packets, rather than only calling link().
 for item in ('gadget_building','gadget_exchanging','gadget_copy_paste'):
  server('''player.teleportTo(0.5,65,-3.5);player.getInventory().clearContent();player.getInventory().setItem(1,new ItemStack(net.minecraft.core.registries.BuiltInRegistries.ITEM.getValue(net.minecraft.resources.Identifier.parse("buildinggadgets2:'''+item+'''"))));return true;''')
  pause()
  rpc('interact.useBlockAt',{'x':0,'y':65,'z':-1,'face':'north'})
  pause()
  for slot in (4,1,2,4):
   rpc('screen.containerClick',{'slot':slot,'button':0,'input':'PICKUP'});time.sleep(.25)
  rpc('screen.close')
  check('wireless access point UI links '+item, '''return GlobalPos.of(level.dimension(),new BlockPos(0,65,-1)).equals(GadgetNBT.getBoundPos(player.getInventory().getItem(1)));''')
 # Keep this bound copy/paste gadget for a real save/restart persistence check.
 server('server.saveEverything(true,true,true);return true;')
 (ROOT/'runs/evidence/ae2-verification.json').write_text(json.dumps(REPORT,indent=2))

def verify_restart():
 REPORT.extend(json.loads((ROOT/'runs/evidence/ae2-verification.json').read_text()))
 check('saved UI binding survives real client and server restart', '''var tool=player.getInventory().getItem(1);return tool.is(Registration.CopyPaste_Gadget.get()) && GlobalPos.of(level.dimension(),new BlockPos(0,65,-1)).equals(GadgetNBT.getBoundPos(tool));''')
 gridcheck('reloaded ME stock and binding remain usable','return storage.getAvailableStacks().get(stone)==64 && BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE)),true,pos,Direction.NORTH);')
 check('disconnect test network power', 'player.getInventory().clearContent();level.setBlockAndUpdate(new BlockPos(-1,65,0),Blocks.AIR.defaultBlockState());return true;')
 pause()
 gridcheck('unpowered access point cannot supply materials', 'return !ap.isActive() && !BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE)),false,pos,Direction.NORTH) && player.getInventory().countItem(Items.STONE)==0;')
 gridcheck('unpowered network returns item to player instead', 'BuildingUtils.giveItemToPlayer(player,new ItemStack(Items.STONE),pos,Direction.NORTH);return player.getInventory().countItem(Items.STONE)==1;')
 check('restore network power','level.setBlockAndUpdate(new BlockPos(-1,65,0),AEBlocks.CREATIVE_ENERGY_CELL.block().defaultBlockState());return true;')
 pause()
 gridcheck('re-powered network retained every item','return ap.isActive() && storage.getAvailableStacks().get(stone)==64;')
 check('missing access point cannot supply materials', 'player.getInventory().clearContent();level.setBlockAndUpdate(new BlockPos(0,65,-1),Blocks.AIR.defaultBlockState());return !BuildingUtils.removeStacksFromInventory(player,List.of(new ItemStack(Items.STONE)),false,GlobalPos.of(level.dimension(),new BlockPos(0,65,-1)),Direction.NORTH);')
 (ROOT/'runs/evidence/ae2-verification.json').write_text(json.dumps(REPORT,indent=2))

def verify_signs():
 REPORT.extend(json.loads((ROOT/'runs/evidence/ae2-verification.json').read_text()))
 for animation in (0,5):
  check('prepare delayed wall-sign cut animation '+str(animation), '''
   player.setGameMode(net.minecraft.world.level.GameType.CREATIVE);player.teleportTo(20.5,65,8.5);
   for(var item:level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,new net.minecraft.world.phys.AABB(18,64,8,230,70,13)))item.discard();
   var a=new BlockPos(20,65,10);var b=a.south();
   for(var q:BlockPos.betweenClosed(a,new BlockPos(219,65,11)))level.setBlockAndUpdate(q,Blocks.AIR.defaultBlockState());
   level.setBlockAndUpdate(a,AEBlocks.QUANTUM_RING.block().defaultBlockState());
   level.setBlockAndUpdate(b,Blocks.OAK_WALL_SIGN.defaultBlockState().setValue(net.minecraft.world.level.block.state.properties.BlockStateProperties.HORIZONTAL_FACING,Direction.SOUTH));
   var sign=(net.minecraft.world.level.block.entity.SignBlockEntity)level.getBlockEntity(b);
   sign.setText(sign.getFrontText().setMessage(0,Component.literal("量子网络-A")),true);
   sign.setText(sign.getBackText().setMessage(0,Component.literal("背面-B")),false);
   var tool=new ItemStack(Registration.CutPaste_Gadget.get());player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,tool);
   GadgetNBT.setRenderType(tool,(byte)'''+str(animation)+''');GadgetNBT.setCopyStartPos(tool,a);GadgetNBT.setCopyEndPos(tool,new BlockPos(219,65,11));
   ((GadgetCutPaste)tool.getItem()).cutAndStore(player,tool);return true;''')
  time.sleep(7)
  check('wall sign survives source support removal '+str(animation), '''
   var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);var id=GadgetNBT.getUUID(player.getMainHandItem());
   return data.getCopyPasteList(id,false).stream().anyMatch(q->q.state.is(Blocks.OAK_WALL_SIGN)) && data.peekTEMap(id).size()==2
    && level.getBlockState(new BlockPos(20,65,10)).isAir() && level.getBlockState(new BlockPos(20,65,11)).isAir();''')
  check('schedule quantum ring and sign paste '+str(animation), '''
   var tool=player.getMainHandItem();var data=com.direwolf20.buildinggadgets2.common.worlddata.BG2Data.get(level);var id=GadgetNBT.getUUID(tool);
   player.teleportTo(224.5,65,8.5);
   for(var q:BlockPos.betweenClosed(224,65,10,224,65,11))level.setBlockAndUpdate(q,Blocks.AIR.defaultBlockState());
   var list=data.getCopyPasteList(id,false);Collections.reverse(list);
   BuildingUtils.buildWithTileData(level,player,list,new BlockPos(224,65,10),data.peekTEMap(id),tool);return true;''')
  time.sleep(4)
  check('quantum label front and back text preserved without duplicate drops '+str(animation), '''
   var be=level.getBlockEntity(new BlockPos(224,65,11));
   return level.getBlockState(new BlockPos(224,65,10)).is(AEBlocks.QUANTUM_RING.block())
    && be instanceof net.minecraft.world.level.block.entity.SignBlockEntity s
    && s.getFrontText().getMessage(0,false).getString().equals("量子网络-A")
    && s.getBackText().getMessage(0,false).getString().equals("背面-B")
    && level.getEntitiesOfClass(net.minecraft.world.entity.item.ItemEntity.class,new net.minecraft.world.phys.AABB(18,64,8,230,70,13)).stream().noneMatch(e->e.getItem().is(Items.OAK_SIGN));''')
 (ROOT/'runs/evidence/ae2-verification.json').write_text(json.dumps(REPORT,indent=2))

if __name__=='__main__':
 import sys
 verify_restart() if '--verify-restart' in sys.argv else verify_signs() if '--verify-signs' in sys.argv else main()

