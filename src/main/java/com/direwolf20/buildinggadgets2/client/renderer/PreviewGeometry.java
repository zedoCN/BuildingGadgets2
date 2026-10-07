package com.direwolf20.buildinggadgets2.client.renderer;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.renderer.StagedVertexBuffer;
import net.minecraft.client.renderer.rendertype.RenderType;

import java.util.LinkedHashMap;
import java.util.Map;

/** Stages the short-lived selection and warning overlays independently of the level's feature draws. */
public final class PreviewGeometry implements AutoCloseable {
    public static final PreviewGeometry INSTANCE = new PreviewGeometry();
    private final StagedVertexBuffer vertices = new StagedVertexBuffer(() -> "BG2 selection overlays", 16384);
    private final Map<RenderType, StagedVertexBuffer.Draw> draws = new LinkedHashMap<>();

    private PreviewGeometry() {}

    public VertexConsumer getBuffer(RenderType type) {
        var draw = draws.computeIfAbsent(type, key -> vertices.appendDraw(key.format(), key.primitiveTopology(),
                key.sortOnUpload() ? RenderSystem.getProjectionType().vertexSorting() : null));
        return vertices.getVertexBuilder(draw);
    }

    @Override
    public void close() {
        vertices.close();
        draws.clear();
    }

    public void endBatch(RenderType type) {
        endBatch();
    }

    public void endBatch() {
        try {
            vertices.upload();
            for (var entry : draws.entrySet()) {
                var info = vertices.getExecuteInfo(entry.getValue());
                if (info != null) entry.getKey().prepare().drawFromBuffer(info);
            }
        } finally {
            draws.clear();
            vertices.endFrame();
        }
    }
}
