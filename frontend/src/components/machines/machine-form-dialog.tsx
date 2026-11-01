import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import type { MachineCreatePayload, MachineRead } from '@/api/types'
import { useCreateMachine, useUpdateMachine } from '@/api/queries'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { titleCase } from '@/lib/format'

const EQUIPMENT_VALUES = [
  'pump',
  'motor',
  'fan',
  'compressor',
  'bearing',
  'gearbox',
  'conveyor',
  'other',
] as const

const machineSchema = z.object({
  identifier: z
    .string()
    .min(2, 'Identifier needs at least 2 characters')
    .max(32, 'Maximum 32 characters')
    .regex(
      /^[A-Za-z0-9][A-Za-z0-9\-_]*$/,
      'Start with a letter or digit; use letters, digits, - or _',
    ),
  name: z.string().min(1, 'Name is required').max(120, 'Maximum 120 characters'),
  equipment_type: z.enum(EQUIPMENT_VALUES),
  location: z.string().max(120, 'Maximum 120 characters'),
  manufacturer: z.string().max(120, 'Maximum 120 characters'),
  model: z.string().max(120, 'Maximum 120 characters'),
  installation_date: z
    .string()
    .refine((value) => value === '' || /^\d{4}-\d{2}-\d{2}$/.test(value), 'Use YYYY-MM-DD'),
  description: z.string().max(2000, 'Maximum 2000 characters'),
})

type MachineFormValues = z.infer<typeof machineSchema>

function toPayload(values: MachineFormValues): MachineCreatePayload {
  return {
    identifier: values.identifier,
    name: values.name,
    equipment_type: values.equipment_type,
    location: values.location.trim() || null,
    manufacturer: values.manufacturer.trim() || null,
    model: values.model.trim() || null,
    installation_date: values.installation_date || null,
    description: values.description.trim() || null,
  }
}

function defaultValues(machine?: MachineRead): MachineFormValues {
  return {
    identifier: machine?.identifier ?? '',
    name: machine?.name ?? '',
    equipment_type: machine?.equipment_type ?? 'pump',
    location: machine?.location ?? '',
    manufacturer: machine?.manufacturer ?? '',
    model: machine?.model ?? '',
    installation_date: machine?.installation_date ?? '',
    description: machine?.description ?? '',
  }
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null
  return <p className="text-xs text-destructive">{message}</p>
}

/** Create (machine undefined) or edit (machine provided) in one dialog. */
export function MachineFormDialog({
  open,
  onOpenChange,
  machine,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  machine?: MachineRead
}) {
  const isEdit = machine !== undefined
  const createMutation = useCreateMachine()
  const updateMutation = useUpdateMachine(machine?.id ?? 0)

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<MachineFormValues>({
    resolver: zodResolver(machineSchema),
    defaultValues: defaultValues(machine),
  })

  useEffect(() => {
    if (open) reset(defaultValues(machine))
  }, [open, machine, reset])

  const pending = createMutation.isPending || updateMutation.isPending

  async function submit(values: MachineFormValues) {
    try {
      if (isEdit) {
        await updateMutation.mutateAsync(toPayload(values))
        toast.success(`Machine ${values.identifier} updated`)
      } else {
        await createMutation.mutateAsync(toPayload(values))
        toast.success(`Machine ${values.identifier} registered`)
      }
      onOpenChange(false)
    } catch (error) {
      if (error instanceof ApiError) {
        const detail = error.details?.find(
          (item) => typeof item.field === 'string' && typeof item.message === 'string',
        )
        if (detail) {
          setError(detail.field as keyof MachineFormValues, { message: detail.message as string })
          return
        }
        if (error.code === 'conflict') {
          setError('identifier', { message: error.message })
          return
        }
        toast.error(error.message)
      } else {
        toast.error('Something went wrong while saving the machine')
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit machine' : 'Register machine'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update identity and asset details. Thresholds are configured separately.'
              : 'Add an asset to the registry. You can configure thresholds and start collecting readings next.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(submit)} className="grid gap-4" noValidate>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label htmlFor="machine-identifier">Identifier</Label>
              <Controller
                control={control}
                name="identifier"
                render={({ field }) => (
                  <Input id="machine-identifier" placeholder="P-101" {...field} />
                )}
              />
              <FieldError message={errors.identifier?.message} />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="machine-name">Name</Label>
              <Controller
                control={control}
                name="name"
                render={({ field }) => (
                  <Input id="machine-name" placeholder="Centrifugal Pump P-101" {...field} />
                )}
              />
              <FieldError message={errors.name?.message} />
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="machine-type">Equipment type</Label>
            <Controller
              control={control}
              name="equipment_type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="machine-type" className="w-full">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {EQUIPMENT_VALUES.map((type) => (
                      <SelectItem key={type} value={type}>
                        {titleCase(type)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            <FieldError message={errors.equipment_type?.message} />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="grid gap-1.5">
              <Label htmlFor="machine-location">Location</Label>
              <Controller
                control={control}
                name="location"
                render={({ field }) => (
                  <Input id="machine-location" placeholder="Hall B, Bay 4" {...field} />
                )}
              />
              <FieldError message={errors.location?.message} />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="machine-manufacturer">Manufacturer</Label>
              <Controller
                control={control}
                name="manufacturer"
                render={({ field }) => (
                  <Input id="machine-manufacturer" placeholder="Acme" {...field} />
                )}
              />
              <FieldError message={errors.manufacturer?.message} />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="machine-model">Model</Label>
              <Controller
                control={control}
                name="model"
                render={({ field }) => <Input id="machine-model" placeholder="T-1" {...field} />}
              />
              <FieldError message={errors.model?.message} />
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="machine-installed">Installation date</Label>
            <Controller
              control={control}
              name="installation_date"
              render={({ field }) => (
                <Input
                  id="machine-installed"
                  type="date"
                  value={field.value}
                  onChange={(event) => field.onChange(event.target.value)}
                />
              )}
            />
            <FieldError message={errors.installation_date?.message} />
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="machine-description">Description</Label>
            <Controller
              control={control}
              name="description"
              render={({ field }) => (
                <Textarea
                  id="machine-description"
                  rows={3}
                  placeholder="Duty point, drive details, monitoring notes…"
                  {...field}
                />
              )}
            />
            <FieldError message={errors.description?.message} />
          </div>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={pending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={pending}>
              {pending ? 'Saving…' : isEdit ? 'Save changes' : 'Register machine'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
