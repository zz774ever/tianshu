import triton
import triton.language as tl
@triton.jit
def triton_poi_fused___and___arange_eq_index_lt_remainder_select_split_where_6(in_ptr0, in_ptr1, out_ptr0, out_ptr1, ks0, ynumel, xnumel, YBLOCK : tl.constexpr, XBLOCK : tl.constexpr):
    xnumel = 32
    # GCU 2D persistent loop: iterate over X tiles, Y handled by grid dim 1
    gridsize_x = tl.num_programs(0)
    xloop_num = (xnumel + XBLOCK - 1) // XBLOCK
    for xloop in range(tl.program_id(0), xloop_num, gridsize_x):
        yoffset = (tl.program_id(1) + tl.program_id(2) * tl.num_programs(1)) * YBLOCK
        yindex = yoffset + tl.arange(0, YBLOCK)[:, None]
        ymask = yindex < ynumel
        xoffset = xloop * XBLOCK
        xindex = xoffset + tl.arange(0, XBLOCK)[None, :]
        xmask = xindex < xnumel
        x1 = xindex
        y0 = yindex
        tmp7 = tl.load(in_ptr0 + (y0 + 2*ks0), ymask, eviction_policy='evict_last')
        tmp21 = tl.load(in_ptr0 + (ks0 + y0), ymask, eviction_policy='evict_last')
        tmp29 = tl.load(in_ptr0 + (y0), ymask, eviction_policy='evict_last')
        tmp0 = (x1 % 3)
        tmp1 = tl.full([1, 1], 2, tl.int64)
        tmp2 = tmp0 == tmp1
        tmp3 = x1
        tmp4 = tl.full([1, 1], 30, tl.int64)
        tmp5 = tmp3 < tmp4
        tmp6 = tmp2 & tmp5
        tmp8 = tl.full([1, 1], 262144, tl.int32)
        tmp9 = tmp7 + tmp8
        tmp10 = tmp7 < 0
        tmp11 = tl.where(tmp10, tmp9, tmp7)
        tl.device_assert(((0 <= tmp11) & (tmp11 < 262144)) | ~(ymask), "index out of bounds: 0 <= tmp11 < 262144")
        tmp13 = tl.load(in_ptr1 + (x1 + 64*tmp11), xmask & ymask).to(tl.float32)
        tmp14 = tmp13.to(tl.bfloat16)
        tmp15 = tmp14.to(tl.float32)
        tmp16 = tl.full([1, 1], 1, tl.int64)
        tmp17 = tmp0 == tmp16
        tmp18 = tl.full([1, 1], 33, tl.int64)
        tmp19 = tmp3 < tmp18
        tmp20 = tmp17 & tmp19
        tmp22 = tmp21 + tmp8
        tmp23 = tmp21 < 0
        tmp24 = tl.where(tmp23, tmp22, tmp21)
        tl.device_assert(((0 <= tmp24) & (tmp24 < 262144)) | ~(ymask), "index out of bounds: 0 <= tmp24 < 262144")
        tmp26 = tl.load(in_ptr1 + (x1 + 64*tmp24), xmask & ymask).to(tl.float32)
        tmp27 = tmp26.to(tl.bfloat16)
        tmp28 = tmp27.to(tl.float32)
        tmp30 = tmp29 + tmp8
        tmp31 = tmp29 < 0
        tmp32 = tl.where(tmp31, tmp30, tmp29)
        tl.device_assert(((0 <= tmp32) & (tmp32 < 262144)) | ~(ymask), "index out of bounds: 0 <= tmp32 < 262144")
        tmp34 = tl.load(in_ptr1 + (x1 + 64*tmp32), xmask & ymask).to(tl.float32)
        tmp35 = tmp34.to(tl.bfloat16)
        tmp36 = tmp35.to(tl.float32)
        tmp37 = tl.where(tmp20, tmp28, tmp36)
        tmp38 = tmp37.to(tl.bfloat16)
        tmp39 = tmp38.to(tl.float32)
        tmp40 = tmp39.to(tl.bfloat16)
        tmp41 = tmp40.to(tl.float32)
        tmp42 = tl.where(tmp6, tmp15, tmp41)
        tmp43 = tmp42.to(tl.bfloat16)
        tmp44 = tmp43.to(tl.float32)
        tmp45 = tl.load(in_ptr1 + (32 + x1 + 64*tmp11), xmask & ymask).to(tl.float32)
        tmp46 = tmp45.to(tl.bfloat16)
        tmp47 = tmp46.to(tl.float32)
        tmp48 = tl.load(in_ptr1 + (32 + x1 + 64*tmp24), xmask & ymask).to(tl.float32)
        tmp49 = tmp48.to(tl.bfloat16)
        tmp50 = tmp49.to(tl.float32)
        tmp51 = tl.load(in_ptr1 + (32 + x1 + 64*tmp32), xmask & ymask).to(tl.float32)
        tmp52 = tmp51.to(tl.bfloat16)
        tmp53 = tmp52.to(tl.float32)
        tmp54 = tl.where(tmp20, tmp50, tmp53)
        tmp55 = tmp54.to(tl.bfloat16)
        tmp56 = tmp55.to(tl.float32)
        tmp57 = tmp56.to(tl.bfloat16)
        tmp58 = tmp57.to(tl.float32)
        tmp59 = tl.where(tmp6, tmp47, tmp58)
        tmp60 = tmp59.to(tl.bfloat16)
        tmp61 = tmp60.to(tl.float32)
        tl.store(out_ptr0 + (x1 + 32*y0), tmp44, xmask & ymask)
        tl.store(out_ptr1 + (x1 + 32*y0), tmp61, xmask & ymask)
