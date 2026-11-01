import { useEffect } from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/api/client'
import type { MachineRead, MachineThresholds, MetricName } from '@/api/types'
import { useUpdateMachine } from '@/api/queries'
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
import { METRIC_META } from '@/lib/format'

const THRESHOLD_METRICS: MetricName[] = [
  'vibration_rms',
  'temperature',
  'rpm',
  'load_pct',
  'pressure',
]

const numberish = z
  .string()
  .refine(
    (value) => value.trim() === '' || (!Number.isNaN(Number(value)) && Number(value) >= 0),
    'Enter a value of 0 or more, or leave blank',
  )

const thresholdSchema = z.object({
  vibration_rms: z.object({ warning: numberish, critical: numberish }),
  temperature: z.object({ warning: numberish, critical: numberish }),
  rpm: z.object({ warning: numberish, critical: numberish }),
  load_pct: z.object({ warning: numberish, critical: numberish }),
  pressure: z.object({ warning: numberish, critical: numberish }),
})

type ThresholdFormValues = z.infer<typeof thresholdSchema>

/** Trim float32 storage noise (7.099999904632568 → 7.1) for the inputs. */
function displayNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return ''
  return String(Number(value.toFixed(6)))
}

function initialValues(machine: MachineRead): ThresholdFormValues {
  const values = {} as ThresholdFormValues
  for (const metric of THRESHOLD_METRICS) {
    const config = machine.thresholds[metric]
    values[metric] = {
      warning: displayNumber(config?.warning),
      critical: displayNumber(config?.critical),
    }
  }
  return values
}

/** Per-machine warning/critical thresholds for every supported metric. */
export function ThresholdsDialog({
  open,
  onOpenChange,
  machine,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  machine: MachineRead
}) {
  const mutation = useUpdateMachine(machine.id)
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<ThresholdFormValues>({
    resolver: zodResolver(thresholdSchema),
    defaultValues: initialValues(machine),
  })

  useEffect(() => {
    if (open) reset(initialValues(machine))
  }, [open, machine, reset])

  async function submit(values: ThresholdFormValues) {
    const thresholds: MachineThresholds = {}
    for (const metric of THRESHOLD_METRICS) {
      const warningRaw = values[metric].warning.trim()
      const criticalRaw = values[metric].critical.trim()
      if (!warningRaw && !criticalRaw) continue
      const warning = warningRaw ? Number(warningRaw) : null
      const critical = criticalRaw ? Number(criticalRaw) : null
      if (warning !== null && critical !== null && critical <= warning) {
        setError(`${metric}.critical`, { message: 'Critical must be greater than warning' })
        return
      }
      thresholds[metric] = { warning, critical }
    }

    try {
      await mutation.mutateAsync({ thresholds })
      toast.success('Thresholds saved')
      onOpenChange(false)
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : 'Could not save thresholds')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Thresholds — {machine.identifier}</DialogTitle>
          <DialogDescription>
            Warning and critical operating limits used by detection. Leave a metric blank to stop
            monitoring it. These are per-machine limits, not certified safety limits.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(submit)} className="grid gap-4" noValidate>
          <div
            className="grid grid-cols-[1fr_7rem_7rem] items-center gap-x-3 gap-y-2 text-xs font-medium text-muted-foreground sm:grid-cols-[1fr_9rem_9rem]"
            aria-hidden
          >
            <span>Metric</span>
            <span className="text-right">Warning</span>
            <span className="text-right">Critical</span>
          </div>

          {THRESHOLD_METRICS.map((metric) => {
            const meta = METRIC_META[metric]
            return (
              <div
                key={metric}
                className="grid grid-cols-[1fr_7rem_7rem] items-start gap-x-3 gap-y-1 sm:grid-cols-[1fr_9rem_9rem]"
              >
                <div className="pt-2">
                  <Label className="text-sm">
                    {meta.label}
                    <span className="ml-1.5 font-normal text-muted-foreground">({meta.unit})</span>
                  </Label>
                </div>
                <Controller
                  control={control}
                  name={`${metric}.warning`}
                  render={({ field }) => (
                    <Input
                      type="number"
                      step="any"
                      min="0"
                      inputMode="decimal"
                      placeholder="—"
                      aria-label={`${meta.label} warning threshold`}
                      className="text-right"
                      {...field}
                    />
                  )}
                />
                <Controller
                  control={control}
                  name={`${metric}.critical`}
                  render={({ field }) => (
                    <Input
                      type="number"
                      step="any"
                      min="0"
                      inputMode="decimal"
                      placeholder="—"
                      aria-label={`${meta.label} critical threshold`}
                      className="text-right"
                      {...field}
                    />
                  )}
                />
                {(errors[metric]?.warning || errors[metric]?.critical) && (
                  <p className="col-span-full text-xs text-destructive sm:col-start-2 sm:col-span-2">
                    {errors[metric]?.warning?.message ?? errors[metric]?.critical?.message}
                  </p>
                )}
              </div>
            )
          })}

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving…' : 'Save thresholds'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
