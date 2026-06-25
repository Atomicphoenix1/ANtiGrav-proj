import type { Meta, StoryObj } from "@storybook/react";
import Button from "./Button";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ['primary'],
    },
    size: {
      control: "select",
      options: ['sm', 'md', 'lg', 'xl'],
    },
    disabled: { control: "boolean" },
    isLoading: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Default: Story = {
  args: {
    children: "Button",
    variant: "primary",
    size: "sm",
  },
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
    { variant: 'primary', children: 'Primary' },
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-wrap items-end gap-4">
    { size: 'sm', children: 'Size SM' },
    { size: 'md', children: 'Size MD' },
    { size: 'lg', children: 'Size LG' },
    { size: 'xl', children: 'Size XL' },
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

export const Loading: Story = {
  args: {
    children: "Loading...",
    isLoading: true,
    variant: "primary",
  },
};

