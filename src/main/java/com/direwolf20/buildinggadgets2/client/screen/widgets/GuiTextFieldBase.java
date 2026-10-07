package com.direwolf20.buildinggadgets2.client.screen.widgets;

import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.network.chat.Component;

import java.util.function.BiConsumer;

public class GuiTextFieldBase extends EditBox {
    private boolean suspended;
    private boolean numericOnly;
    private String lastValidValue = "";
    private String valueDefault, valueOld;
    private BiConsumer<GuiTextFieldBase, String> postModification;

    public GuiTextFieldBase(Font fontRenderer, int x, int y, int width) {
        super(fontRenderer, x, y, width, 15, Component.empty());

        setMaxLength(50);
        setResponder(value -> {
            if (!accepts(value)) {
                int cursor = getCursorPosition();
                super.setValue(lastValidValue);
                setCursorPosition(Math.max(0, cursor - 1));
                return;
            }
            valueOld = lastValidValue;
            lastValidValue = value;
            postModification(value);
        });
    }

    @Override
    public void setValue(String textIn) {
        if (accepts(textIn)) super.setValue(textIn);
    }

    private boolean accepts(String value) {
        if (!numericOnly || value.isEmpty() || "-".equals(value)) return true;
        try {
            Integer.parseInt(value);
            return true;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }

    public void postModification(String text) {
        if (!suspended && postModification != null) {
            suspended = true;
            postModification.accept(this, valueOld);
            suspended = false;
        }
    }

    public GuiTextFieldBase restrictToNumeric() {
        numericOnly = true;

        return this;
    }

    public int getInt() {
        try {
            return Integer.parseInt(getValue());
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    public GuiTextFieldBase setDefaultInt(int defaultInt) {
        return setDefaultValue(Integer.toString(defaultInt));
    }

    public GuiTextFieldBase setDefaultValue(String defaultValue) {
        this.valueDefault = defaultValue;
        return this;
    }
}
