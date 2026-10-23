import * as React from "react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "./sheet";

export interface DrawerProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children?: React.ReactNode;
}

export function Drawer({ open, onOpenChange, children }: DrawerProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      {children}
    </Sheet>
  );
}

export const DrawerTrigger = SheetTrigger;
export const DrawerHeader = SheetHeader;
export const DrawerTitle = SheetTitle;
export const DrawerDescription = SheetDescription;

export function DrawerContent({
  className,
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof SheetContent>) {
  return (
    <SheetContent side="bottom" className={className} {...props}>
      {children}
    </SheetContent>
  );
}
