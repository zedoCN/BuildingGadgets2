package com.direwolf20.buildinggadgets2.verification;

import com.direwolf20.buildinggadgets2.common.worlddata.BG2Data;
import com.direwolf20.buildinggadgets2.common.network.data.RelativePastePayload;
import com.direwolf20.buildinggadgets2.common.network.data.DestructionRangesPayload;
import com.direwolf20.buildinggadgets2.util.datatypes.StatePos;
import com.direwolf20.buildinggadgets2.util.datatypes.TagPos;
import com.google.common.collect.HashBiMap;
import io.netty.buffer.Unpooled;
import net.minecraft.SharedConstants;
import org.junit.jupiter.api.Test;
import net.minecraft.server.Bootstrap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.NbtOps;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.UUID;

/** Regression checks for data that must survive multiplayer transport and world saves. */
public final class PortDataTest {
    private static int checks;
    private static void check(boolean value, String reason) {
        if (!value) throw new AssertionError(reason);
        checks++;
    }
    @Test
    public void persistedDataAndPayloadsRoundTrip() {
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        var states = new ArrayList<StatePos>(List.of(
            new StatePos(Blocks.STONE.defaultBlockState(), new BlockPos(-2, 64, -1)),
            new StatePos(Blocks.OAK_STAIRS.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.NORTH), new BlockPos(-1, 64, -1)),
            new StatePos(Blocks.AIR.defaultBlockState(), new BlockPos(-2, 64, 0)),
            new StatePos(Blocks.GLASS.defaultBlockState(), new BlockPos(-1, 64, 0))));
        for (var state : states) check(state.equals(new StatePos(state.getTag())), "block-state and negative coordinates NBT round trip");
        check(states.equals(BG2Data.statePosListFromNBTMapArray(BG2Data.statePosListToNBTMapArray(states))), "copy template palette round trip");
        var machine = new CompoundTag();
        machine.putString("id", "minecraft:chest"); machine.putInt("energy", 123456);
        var originalTag = new TagPos(machine, new BlockPos(-2, 64, -1));
        check(originalTag.equals(new TagPos(originalTag.getTag())), "machine block entity NBT round trip");
        var tags = new ArrayList<TagPos>(List.of(originalTag));
        var rotated = states;
        for (int i=0;i<4;i++) rotated=StatePos.rotate90Degrees(rotated,tags);
        check(states.equals(rotated), "four rotations preserve positions and directional block state");
        check(tags.getFirst().equals(originalTag), "four rotations preserve machine NBT position");
        var id = UUID.randomUUID();
        var undo = new HashMap<UUID,ArrayList<StatePos>>(); undo.put(id,states);
        var copies = new HashMap<UUID,ArrayList<StatePos>>(); copies.put(id,states);
        var machines = new HashMap<UUID,ArrayList<TagPos>>(); machines.put(id,tags);
        var prints = HashBiMap.<UUID,String>create(); prints.put(id,"regression-template");
        var saved = new BG2Data(undo,copies,machines,prints);
        var nbt = BG2Data.CODEC.encodeStart(NbtOps.INSTANCE,saved).getOrThrow();
        var restored=BG2Data.CODEC.parse(NbtOps.INSTANCE,nbt).getOrThrow();
        check(restored.peekUndoList(id).equals(states),"undo persists through SavedData codec");
        check(restored.getCopyPasteList(id,false).equals(states),"copy template persists through SavedData codec");
        check(restored.peekTEMap(id).equals(tags),"machine NBT persists through SavedData codec");
        check(id.equals(restored.getRedprintUUIDfromName("regression-template")),"named template persists through SavedData codec");
        check(restored.removeFromRedprints("regression-template") && restored.getCopyPasteList(id,false)==null && restored.peekTEMap(id)==null,"deleting template clears its saved contents");
        var empty1=BG2Data.CODEC.parse(NbtOps.INSTANCE,new CompoundTag()).getOrThrow();
        var empty2=BG2Data.CODEC.parse(NbtOps.INSTANCE,new CompoundTag()).getOrThrow();
        empty1.addToCopyPaste(id,states);
        check(empty2.getCopyPasteList(id,false)==null,"worlds do not share codec defaults");
        var buf = new FriendlyByteBuf(Unpooled.buffer());
        try {
            var payload=new RelativePastePayload(new BlockPos(-30, -64, 200));
            RelativePastePayload.STREAM_CODEC.encode(buf,payload);
            check(RelativePastePayload.STREAM_CODEC.decode(buf).equals(payload) && !buf.isReadable(),"relative paste network codec");
            var ranges=new DestructionRangesPayload(1, 2, 3, 4, 5);
            DestructionRangesPayload.STREAM_CODEC.encode(buf,ranges);
            check(DestructionRangesPayload.STREAM_CODEC.decode(buf).equals(ranges) && !buf.isReadable(),"destruction range network codec");
        } finally { buf.release(); }
        System.out.println("PASS " + checks + " port data checks");
    }
}
