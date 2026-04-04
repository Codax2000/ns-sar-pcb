'''
Script: diagrams

This script is meant to be used to draw all the technical diagrams for
this project. This includes:

- Silva-Steensgard Theory
- Toplevel Schematics
- Digital Architecture
- Main State Machine
- Analog Comparator
- SAR Logic
- FPGA/PCB Floorplanning
- SPI Packet structure

'''

import schemdraw
import schemdraw.elements as elm
from schemdraw import dsp
from schemdraw import flow
from schemdraw import logic


'''
Function: draw_digital_architecture

Draw and saves the ADC digital architecture

Parameters:
    filename - the name of the PNG file in ./docs/docs/img that will be saved
'''
def draw_digital_architecture(filename='digital.png'):
    with schemdraw.Drawing(show=False) as d:
        elm.DataBusLine().dot()
        with d.hold():
            elm.Line().length(d.unit/4)
            spi = dsp.Box(w=2, h=2).anchor('W').label('SPI')
        dsp.Line().down()
        dsp.Line().right().label('SCL').dot().length(d.unit*2/3)
        
        # add SCL line to data memory
        with d.hold():
            dsp.Line().down()
            dsp.Line().right().length(d.unit*2.15)
            datamem = elm.Ic(
                pins=[elm.IcPin(name='>', side='left', slot='1/3'),
                    elm.IcPin(name='RD', side='left', slot='3/3'),
                    elm.IcPin(name='WR', side='right', slot='3/3')]
            ).anchor('>').label('MEM')

        dsp.Line().right().length(d.unit/3)
        reset = dsp.Box(w=1,h=1).label('RST')

        # create registers
        dbl = elm.DataBusLine().at(spi.E, dy=0.5).label('REG IF')
        reg = dsp.Box(w=2, h=2).at(dbl.end, dy=-0.5).label('REG')

        dsp.Line().at(spi.E, dy=-0.5).tox(reset.N)
        elm.DataBusLine().length(d.unit/2).down()
        dsp.Arrow().toy(reset.N).length(d.unit/2)
        dsp.Line().at(reset.E).length(d.unit/4).right()
        dsp.Line().up().toy(reg.W - 0.5).label('Reg reset', rotate=True)
        dsp.Arrow().right().tox(reg.W)

        # connect registers to synchronizers and memory
        dsp.Arrow().at(reg.E, dy=0.5).length(d.unit/2)
        sysclk_sync = dsp.Box(h=1,w=2).label('Sync to\nPLL clock')
        spiclk_sync = dsp.Box(h=1,w=2).at(sysclk_sync.S).anchor('N').label('Sync to\nSPI clock')
        dsp.Arrow().tox(reg.E).at(spiclk_sync.W)
        dsp.Line().at(datamem.RD).up().toy(spiclk_sync.W-0.1*d.unit).label('Mem read', rotate=True)
        dsp.Arrow().left().tox(reg.E)

        # create main state machine and connect it up
        dsp.Line().at(sysclk_sync.E).right().length(d.unit/2).dot()
        arr1 = dsp.Arrow().right().length(d.unit/2)
        main_sm = dsp.Box(h=3).at(arr1.end, dy=-1).label('Main State\nMachine')
        dsp.Arrow().at(main_sm.W).tox(spiclk_sync.E)

        # create and connect PLL
        dsp.Line().at(main_sm.S).length(d.unit/4).down()
        pll = dsp.Box(h=1,w=1).label('PLL').anchor('N')
        dsp.Line().at(pll.W, dy=0.25).left().length(d.unit/2)
        dsp.Line().up().toy(spiclk_sync.E).dot()
        dsp.Line().at(arr1.start).down().toy(pll.W-0.25)
        dsp.Line().tox(pll.W)
        dsp.Line().at(pll.E).right().label('Ref clock', loc='right').length(d.unit*2)

        # create dividing lines
        dsp.Line().at(datamem.RD, dx=0.2).up().toy(reg.N + 0.5).style(color='gray', ls='--')
        dsp.Line().at(datamem.RD, dx=0.2).down().style(color='gray', ls='--').length(d.unit*3/4)
        dsp.Line().at(datamem.WR, dx=-0.2).up().toy(reg.N + 0.5).style(color='gray', ls='--')
        dsp.Line().at(datamem.WR, dx=-0.2).down().style(color='gray', ls='--').length(d.unit*3/4)\
            .label('SPI Clock Domain', halign='right', ofst=(1.25, -3.5))\
            .label('CDC', halign='center', ofst=(1.25, -1.5))\
            .label('PLL Clock Domain', halign='left', ofst=(1.25, 0.5))
        
        # create DSP mux into memory
        dsp.Line().at(datamem.WR).right().length(d.unit/2)
        dmux = elm.intcircuits.Multiplexer(
            demux=True, 
            size=(0.5,1),
            pins=[elm.IcPin(anchorname='D', side='left'),
                elm.IcPin(anchorname='A', side='right'),
                elm.IcPin(anchorname='B', side='right')],
            edgepadH=0,
            edgepadW=0,
            lsize=0).anchor('D')
        dsp.Box(h=0.5, w=4).label('Incremental Filters').at(dmux.A)
        dsp.Line().length(d.unit/8)
        fl = dsp.Line().up().length(d.unit/6).dot()
        dsp.Line().at(dmux.B).tox(fl.end).right()
        dsp.Line().down().toy(fl.end)

        # main state machine to SAR state machine
        dsp.Line().at(main_sm.E).length(d.unit).right().dot()
        with d.hold():
            dsp.Line().length(d.unit/4)
            sar_sm = dsp.Box().anchor('W').label('SAR State\nMachine')
            dsp.Arrow().at(sar_sm.E, dx=1).left().tox(sar_sm.E).label('Comparator Input', loc='right')
            dsp.Line().at(sar_sm.N).up().length(d.unit/4)
            elm.DataBusLine().right().length(d.unit/2)
            dsp.Arrow().length(d.unit/2 - 0.5).label(r'$I^2C$ to Shift Registers', loc='right')
        elm.DataBusLine().down().toy(fl.end)
        dsp.Line().left().tox(fl.end)
    
    d.save(f'./docs/docs/img/{filename}')


'''
Function: draw_adc_loop

Draws the Silva-Steensgard ADC loop used in the design
'''
def draw_adc_loop(filename='adc_loop'):
    with schemdraw.Drawing(show=False) as d:
        d.unit = 1
        dsp.Line().length(d.unit/2).dot().label(r'$V_{in}$')
        
        with d.hold():
            # draw sum and first filter
            dsp.Arrow().length(d.unit/2)
            sum_err = dsp.Sum().anchor('W')
            dsp.Arrow().length(d.unit/2)
            filt1 = dsp.Box(h=1.5,w=2).label(r'$\frac{1}{1-z^{-1}}$', fontsize=18)

            # draw second filter
            f1_out = dsp.Line().length(d.unit/2).dot()
            dsp.Arrow().length(d.unit/2)
            filt2 = dsp.Box(h=1.5,w=2).label(r'$\frac{1}{1-z^{-1}}$', fontsize=18)

            # draw final delay and quantizer
            dsp.Arrow().length(d.unit/2)
            del2 = dsp.Box(h=1,w=1.5).label(r'$z^{-1}$')
            dsp.Arrow().length(d.unit/2)
            s_quant = dsp.Sum().anchor('W')
            dsp.Arrow().length(d.unit/2)

            dsp.Adc().label('SAR')
            elm.DataBusLine().length(d.unit*3/2).dot()

            with d.hold():
                dsp.Arrow().label('To Digital', loc='right').length(d.unit)

            # draw feedback
            dsp.Line().down().length(d.unit*2)
            dsp.Line().left()
            dsp.Box(h=1,w=1.5).label('DWA')
            dsp.Line().tox(filt1.E)
            dsp.Dac().label('CDAC')
            dsp.Line().tox(sum_err.S)
            dsp.Arrow().toy(sum_err.S).up()\
                .label('-', ofst=(0.6,0.25), fontsize=24)
            
        # now that we're back at start, draw feedforward
        dsp.Line().up().length(d.unit*2.5)
        dsp.Line().right().tox(s_quant.N)
        dsp.Arrow().to(s_quant.N)

        dsp.Line().up().length(d.unit*3/2).at(f1_out.end)
        dsp.Arrow().right().tox(del2.W)
        dsp.Box(h=1,w=1.5).label(r'$z^{-1}$')
        dsp.Line().length(d.unit/4)
        dsp.Arrow().to(s_quant.NW)
    
    d.save(f'./docs/docs/img/{filename}')

'''
Function: draw_digital_filter

Draw incremental filters (implemented as up-counters with resets)
'''
def draw_digital_filter(filename='dig_filter.png'):
    with schemdraw.Drawing(show=False) as d:
        d.unit=1
        dsp.Arrow().length(d.unit).label(r'$D_1$', loc='left')
        filt1 = dsp.Box(h=1.5,w=2).label(r'$\frac{1}{1-z^{-1}}$', fontsize=18)
        dsp.Arrow().length(d.unit)
        filt2 = dsp.Box(h=1.5,w=2).label(r'$\frac{1}{1-z^{-1}}$', fontsize=18)
        dsp.Arrow().length(d.unit)
        ds = dsp.Box(h=1.5,w=2).label(r'$\downarrow OSR$', fontsize=18)
        dsp.Arrow().length(d.unit).label('To Data Mem', loc='right')

        dsp.Arrow().at(filt1.S, dy=-d.unit/2).to(filt1.S).label('RST', loc='left')
        dsp.Arrow().at(filt2.S, dy=-d.unit/2).to(filt2.S).label('RST', loc='left')
    
    d.save(f'./docs/docs/img/{filename}')


'''
Function: draw_uvm_tb
'''
def draw_uvm_db(filename='uvm_tb.png'):
    with schemdraw.Drawing(show=False) as d:
        dsp.Box().label('VIN Agent').fill('navajowhite')
        dsp.Arrow().label(r'$V_{in}[k]$')
        ana = dsp.Box().label('SV Analog\n(Model)')
        dsp.Arrow().label('Comparator\nOutput')
        dut = dsp.Box().label('ADC RTL\n(DUT)')
        elm.DataBusLine().label('SPI')
        spi = dsp.Box().label('SPI Agent').fill('navajowhite')
        dsp.Arrow(double=True).length(d.unit/2)
        dsp.Box().label("UVM RAL").fill('lightblue')

        with d.hold():
            dsp.Line().length(d.unit/2).at(dut.N).up().label(r'$I^2C$')
            dsp.Line().left().length(d.unit/3)
            cpsr = dsp.Box(h=1).label('CP Shift Register\n(Model)')
            elm.DataBusLine().tox(ana.N)
            dsp.Arrow().toy(ana.N).label(r'CP $V_{DAC}$')

        with d.hold():
            dsp.Line().length(d.unit/2).at(dut.S).down().label(r'$I^2C$')
            dsp.Line().left().length(d.unit/3)
            cnsr = dsp.Box(h=1).label('CN Shift Register\n(Model)')
            elm.DataBusLine().tox(ana.S)
            dsp.Arrow().toy(ana.S).label(r'CN $V_{DAC}$')

        clkgen = dsp.Box(h=1).anchor('N').at(dut.S, dx=0.5, dy=-d.unit).label('CLKGEN Agent').fill('navajowhite')
        dsp.Arrow().at(clkgen.N).up().toy(dut.S)
        rst = dsp.Box(h=1).anchor('N').at(clkgen.S, dx=0.65).label('RESET Agent').fill('navajowhite')
        dsp.Line().at(rst.N).up().toy(clkgen.N).linestyle(':')
        dsp.Arrow().toy(dut.S)

        # boundary lines
        b = 0.35
        dsp.Line().at(ana.W, dx=-b).up().toy(cpsr.N + b).linestyle('--').color('gray')
        dsp.Line().right().tox(dut.E + b).linestyle('--').color('gray')\
            .label('Planned PCB')
        dsp.Line().down().toy(cnsr.S - b).linestyle('--').color('gray')
        dsp.Line().left().tox(ana.W - b).linestyle('--').color('gray')
        dsp.Line().up().toy(ana.W).linestyle('--').color('gray')
    d.save(f'./docs/docs/img/{filename}')


'''
Function: draw_main_sm
'''
def draw_main_sm(filename='main_state_machine.png'):
    with schemdraw.Drawing(show=False) as d:
        flow.Arrow().down().length(d.unit/4).label('Reset', loc='right')
        ready = flow.Box().label('Ready')
        flow.Arrow().at(ready.E).right().label('Start = 1')
        sh_active = flow.Box().label('SH')
        flow.Arrow()
        with d.container() as sar:
            sq = flow.Box().label('SAR Quantize')
            flow.Arrow(double=True).length(d.unit/2)
            flow.Box().label(r'Shift Register\n$I^2C$')
            sar.color('blue')
            sar.linestyle('--')
            sar.label('SAR Conversion', loc='N', halign='center', valign='top')
        flow.Line().length(d.unit/2)
        flow.Arrow().down().length(d.unit/2)
        
        ns_en = flow.Decision(W='No', S='Yes').label('Integration\nEnabled?')
        arr1 = flow.Arrow().at(ns_en.W).left().tox(sh_active.E)
        nfft_done = flow.Decision(N='No', W='Yes').anchor('E').label('NFFT\nDone')
        flow.Arrow().at(nfft_done.N).up().toy(sh_active.S)
        done = flow.Box().at((ready.E[0], nfft_done.W[1])).anchor('E').label('Done')
        flow.Arrow().at(done.N).up().to(ready.S).label('Start = 0', loc='bottom')
        flow.Arrow().at(nfft_done.W).left()

        flow.Line().at(ns_en.S).down().length(d.unit/2)
        flow.Arrow().left().length(d.unit/2)
        flow.Box().label('INT1')
        flow.Arrow()
        flow.Box().label('INT2')
        flow.Line().tox(nfft_done.S)
        flow.Arrow().toy(nfft_done.S)
    d.save(f'./docs/docs/img/{filename}')


'''
Function: draw_spi
'''
def draw_spi(filename='spi'):
    with schemdraw.Drawing(show=False) as d:
        logic.TimingDiagram(
            {'signal': [
                {'name': r'$\overline{CS}$', 'wave': '1.0.................'},
                {'name': 'SCLK',             'wave': 'xln.................'},
                {'name': 'MOSI',             'wave': 'x.322222224222222222', 
                'data': ['RD', 'BC0', 'BC1', 'BC2', 'BC3', 'BC4', 'BC5', 'BC6', 'P',
                        'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'P']},
                {'name': 'MISO',             'wave': 'z.........4z.......4', 'data': ['P', 'P']}
            ]},
            grid=False,
            ygap=0.4
        )
    d.save(f'./docs/docs/img/{filename}_header.png')

    with schemdraw.Drawing(show=False) as d:
        logic.TimingDiagram(
            {'signal': [
                {'name': r'$\overline{CS}$', 'wave': '1.0..|....|....|....|..1'},
                {'name': 'SCLK',             'wave': 'xln..|....|....|....|.lx'},
                {'name': 'MOSI',             'wave': 'x.2..|32..|32..|32..|3x.',
                'data': ['HEADER', 'P', 'ADDR[0:7]', 'P', 'ADDR[8:15]', 'P', 'WR DATA [0:7]', 'P']},
                {'name': 'MISO',             'wave': 'z....|4z..|4z..|4z..|4z.', 'data': ['P'] * 4}
            ],
            'edge': [
                '[2^:17]+[2^:22] Repeat $BC+1$ Times'
            ]},
            grid=False,
            ygap=0.4
        )
    d.save(f'./docs/docs/img/{filename}_write_packet.png')

    with schemdraw.Drawing(show=False) as d:
        logic.TimingDiagram(
            {'signal': [
                {'name': r'$\overline{CS}$', 'wave': '1.0..|....|....|....|..1'},
                {'name': 'SCLK',             'wave': 'xln..|....|....|....|.lx'},
                {'name': 'MOSI',             'wave': 'x.2..|32..|32..|3x..|3x.',
                'data': ['HEADER', 'P', 'ADDR[0:7]', 'P', 'ADDR[8:15]', 'P', 'P']},
                {'name': 'MISO',             'wave': 'z....|4z..|4z..|42..|4z.', 'data': ['P'] * 3 + ['RD DATA [0:7]', 'P']}
            ],
            'edge': [
                '[3^:17]+[3^:22] Repeat $BC+1$ Times'
            ]},
            grid=False,
            ygap=0.4
        )
    d.save(f'./docs/docs/img/{filename}_read_packet.png')

def main():
    draw_digital_architecture()
    draw_adc_loop()
    draw_digital_filter()
    draw_uvm_db()
    draw_main_sm()
    draw_spi()

if __name__ == '__main__':
    main()