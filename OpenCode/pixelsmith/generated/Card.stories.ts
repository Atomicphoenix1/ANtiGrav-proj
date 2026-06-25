import type { Meta, StoryObj } from "@storybook/react";
import Card from "./Card";

const meta: Meta<typeof Card> = {
  title: "UI/Card",
  component: Card,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ['default', 'bordered', 'elevated'],
    },
    size: {
      control: "select",
      options: ['md'],
    },
    disabled: { control: "boolean" },
    
  },
};

export default meta;
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  args: {
    children: "Card",
    variant: "default",
    size: "md",
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
    { variant: 'default', children: 'Default' },
    { variant: 'bordered', children: 'Bordered' },
    { variant: 'elevated', children: 'Elevated' },
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-wrap items-end gap-4">
    { size: 'md', children: 'Size MD' },
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    children: "Disabled",
    disabled: true,
    variant: "primary",
  },
};

